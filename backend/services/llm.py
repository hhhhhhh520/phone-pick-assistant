import httpx
import json
import logging
from backend.config import get_settings
from typing import AsyncGenerator, List, Dict

settings = get_settings()
logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """估算文本的token数量（简化实现：字符数/2）"""
    if not text:
        return 0
    return len(text) // 2


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
        logger.info(f"Truncated messages: kept {max_messages} of {len(messages)} messages")

    # 按max_tokens截断
    result = system_messages + regular_messages
    total_tokens = sum(estimate_tokens(m.get("content", "")) for m in result)

    if total_tokens > max_tokens:
        # 从普通消息中移除最旧的，直到满足token限制
        while regular_messages and total_tokens > max_tokens:
            removed = regular_messages.pop(0)
            total_tokens -= estimate_tokens(removed.get("content", ""))
            logger.info(f"Removed message to fit token limit: {total_tokens} tokens remaining")
        result = system_messages + regular_messages

    return result


class LLMError(Exception):
    """LLM服务错误"""
    pass


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,  # 最小化token消耗
                        "stream": False
                    },
                    timeout=10.0  # 健康检查使用较短超时
                )

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
        """流式对话"""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        logger.debug(f"LLM request: model={self.model}, messages={len(messages)}")

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

    async def chat(self, messages: List[Dict], system_prompt: str = None) -> str:
        """非流式对话"""
        result = ""
        async for chunk in self.chat_stream(messages, system_prompt):
            result += chunk
        logger.debug(f"LLM response length: {len(result)}")
        return result
