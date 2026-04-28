import httpx
import json
from backend.config import get_settings
from typing import AsyncGenerator, List, Dict

settings = get_settings()


class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    async def chat_stream(self, messages: List[Dict], system_prompt: str = None) -> AsyncGenerator[str, None]:
        """流式对话"""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

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
        return result
