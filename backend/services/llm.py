import httpx
import json
import logging
import re
from backend.config import get_settings
from typing import AsyncGenerator, List, Dict, Optional

settings = get_settings()
logger = logging.getLogger(__name__)

ANTHROPIC_VERSION = "2023-06-01"


def extract_anthropic_text_delta(line: str) -> Optional[str]:
    """从 Anthropic Messages SSE 的 data 行提取正文增量

    只认 content_block_delta 事件里的 text_delta；thinking_delta（思考过程）、
    message_start/message_stop 等一律返回 None，保证思考内容不进用户回复。
    """
    if not line.startswith("data: "):
        return None
    try:
        data = json.loads(line[6:])
    except json.JSONDecodeError:
        return None
    if data.get("type") != "content_block_delta":
        return None
    delta = data.get("delta") or {}
    if delta.get("type") == "text_delta":
        return delta.get("text") or None
    return None


def estimate_tokens(text: str) -> int:
    """Estimate token count. Uses tiktoken when available, with layered fallbacks."""
    if not text:
        return 0
    try:
        return _estimate_tiktoken(text)
    except Exception:
        try:
            return _estimate_lang_aware(text)
        except Exception:
            return _estimate_simple(text)


def _estimate_tiktoken(text: str) -> int:
    import tiktoken
    for enc_name in ["cl100k_base", "o200k_base"]:
        try:
            enc = tiktoken.get_encoding(enc_name)
            return len(enc.encode(text))
        except Exception:
            continue
    raise RuntimeError("No tiktoken encoding available")


def _estimate_lang_aware(text: str) -> int:
    chinese = len(re.findall(r'[一-鿿]', text))
    english = len(re.findall(r'[a-zA-Z]', text))
    other = len(text) - chinese - english
    return int(chinese * 1.5 + english * 0.25 + other * 0.5)


def _estimate_simple(text: str) -> int:
    return len(text) // 2


def _detect_estimation_method() -> str:
    """Detect which token estimation method is currently active."""
    try:
        import tiktoken
        for enc_name in ["cl100k_base", "o200k_base"]:
            try:
                tiktoken.get_encoding(enc_name)
                return "tiktoken"
            except Exception:
                continue
        return "language-aware"
    except Exception:
        return "simple"


def truncate_messages(
    messages: List[Dict],
    max_tokens: int = None,
    max_messages: int = None
) -> List[Dict]:
    """
    截断消息列表以满足token和数量限制

    Args:
        messages: 消息列表
        max_tokens: 最大token数（默认使用配置）
        max_messages: 最大消息数（默认使用配置）

    Returns:
        截断后的消息列表，保留系统消息
    """
    est_method = _detect_estimation_method()
    max_tokens = max_tokens or settings.max_context_tokens
    max_messages = max_messages or settings.max_context_messages

    if not messages:
        return messages

    # 分离系统消息和普通消息
    system_messages = [m for m in messages if m.get("role") == "system"]
    regular_messages = [m for m in messages if m.get("role") != "system"]

    # 按max_messages截断（保留最新的消息）
    if len(regular_messages) > max_messages:
        regular_messages = regular_messages[-max_messages:]
        logger.info(
            f"Truncated messages [{est_method}]: kept {max_messages} of "
            f"{len(messages)} messages"
        )

    # 按max_tokens截断
    result = system_messages + regular_messages
    total_tokens = sum(estimate_tokens(m.get("content", "")) for m in result)

    if total_tokens > max_tokens:
        # 从普通消息中移除最旧的，直到满足token限制
        while regular_messages and total_tokens > max_tokens:
            removed = regular_messages.pop(0)
            total_tokens -= estimate_tokens(removed.get("content", ""))
            logger.info(
                f"Removed message to fit token limit [{est_method}]: "
                f"{total_tokens} tokens remaining"
            )
        result = system_messages + regular_messages

    return result


class LLMError(Exception):
    """LLM服务错误"""
    pass


class LLMService:
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.protocol = settings.llm_api_protocol.lower()
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    async def health_check(self) -> dict:
        """
        轻量级LLM健康检查

        通过发送最小化请求验证API可达性和API Key有效性。
        使用最小的token消耗（仅发送一条空消息获取模型响应）。

        Returns:
            dict: {"status": "available"|"error", "model": str, "error": str|None}
        """
        if self.protocol == "anthropic":
            url = f"{self.base_url}/v1/messages"
            payload: Dict = {
                "model": self.model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
                "stream": False,
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "anthropic-version": ANTHROPIC_VERSION}
        else:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,  # 最小化token消耗
                "stream": False
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)

                if response.status_code == 200:
                    return {
                        "status": "available",
                        "model": self.model,
                        "error": None
                    }
                elif response.status_code == 401:
                    return {
                        "status": "error",
                        "model": self.model,
                        "error": "API Key无效或已过期"
                    }
                elif response.status_code == 429:
                    # 速率限制也算可达，只是暂时受限
                    return {
                        "status": "available",
                        "model": self.model,
                        "error": "API速率受限，但服务可达"
                    }
                else:
                    error_detail = response.text[:100] if response.text else "未知错误"
                    return {
                        "status": "error",
                        "model": self.model,
                        "error": f"API错误 ({response.status_code}): {error_detail}"
                    }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "model": self.model,
                "error": "API连接超时"
            }
        except httpx.ConnectError:
            return {
                "status": "error",
                "model": self.model,
                "error": "无法连接到API服务"
            }
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return {
                "status": "error",
                "model": self.model,
                "error": str(e)[:100]
            }

    async def chat_stream(self, messages: List[Dict], system_prompt: str = None) -> AsyncGenerator[str, None]:
        """流式对话（按 llm_api_protocol 分发到对应协议实现）"""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        logger.debug(f"LLM request: protocol={self.protocol}, model={self.model}, messages={len(messages)}")

        if self.protocol == "anthropic":
            async for chunk in self._chat_stream_anthropic(messages):
                yield chunk
        else:
            async for chunk in self._chat_stream_openai(messages):
                yield chunk

    @staticmethod
    def _split_system_messages(messages: List[Dict]) -> tuple:
        """拆出 system 消息（Anthropic 协议要求 system 是顶层字段），并合并相邻同角色消息

        Anthropic Messages API 不接受连续同角色消息（如历史末尾的 user
        再追加一条 user 角色 prompt），合并既满足协议又保持语义。
        """
        system_parts = [m.get("content", "") for m in messages if m.get("role") == "system"]
        rest = [m for m in messages if m.get("role") != "system"]

        merged: List[Dict] = []
        for msg in rest:
            if merged and merged[-1].get("role") == msg.get("role"):
                merged[-1]["content"] = merged[-1].get("content", "") + "\n\n" + msg.get("content", "")
            else:
                merged.append(dict(msg))
        system_text = "\n\n".join(p for p in system_parts if p)
        return (system_text or None), merged

    @staticmethod
    def _build_anthropic_payload(messages: List[Dict], max_tokens: int, temperature: float, model: str, stream: bool) -> Dict:
        system, msgs = LLMService._split_system_messages(messages)
        payload: Dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            "messages": msgs,
        }
        if system:
            payload["system"] = system
        return payload

    async def _chat_stream_anthropic(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """Anthropic Messages 协议流式（火山方舟编程套餐等），过滤 thinking 增量只输出正文"""
        payload = self._build_anthropic_payload(messages, self.max_tokens, self.temperature, self.model, True)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": ANTHROPIC_VERSION,
        }
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        logger.error(f"LLM API error: {response.status_code}, {error_body}")
                        raise LLMError(f"API error: {response.status_code}, {error_body.decode()}")
                    async for line in response.aiter_lines():
                        delta = extract_anthropic_text_delta(line)
                        if delta:
                            yield delta
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"LLM anthropic_stream error: {type(e).__name__}: {e}")
            raise

    async def _chat_stream_openai(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """OpenAI 兼容协议流式（DeepSeek 等）"""
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "stream": True
                    },
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        logger.error(f"LLM API error: {response.status_code}, {error_body}")
                        raise LLMError(f"API error: {response.status_code}, {error_body.decode()}")
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                data = json.loads(line[6:])
                                if data.get("choices") and data["choices"][0].get("delta", {}).get("content"):
                                    yield data["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"LLM chat_stream error: {type(e).__name__}: {e}")
            raise

    async def chat(self, messages: List[Dict], system_prompt: str = None) -> str:
        """非流式对话"""
        result = ""
        async for chunk in self.chat_stream(messages, system_prompt):
            result += chunk
        logger.debug(f"LLM response length: {len(result)}")
        return result
