from backend.services.llm import LLMService, truncate_messages
from backend.models.domain import Phone
from backend.config import get_settings
from typing import List, AsyncGenerator, Dict, Optional
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


RECOMMEND_PROMPT = """你是一个专业的手机选购顾问。

用户需求: {user_need}
候选手机列表:
{phones}

请根据用户需求，从上面的候选手机列表中推荐最合适的2-3款手机。
重要：你只能推荐上面列表中的手机，不要推荐列表之外的手机。
说明推荐理由，用简洁自然的语言回答。
"""

COMPARE_PROMPT = """你是一个手机参数对比专家。

用户想对比以下手机:
{phones}

请从以下维度对比:
1. 性能(处理器、内存)
2. 拍照(摄像头配置)
3. 续航(电池、充电)
4. 价格

用简洁语言总结差异，给出选择建议。
"""


class RecommendService:
    def __init__(self):
        self.llm = LLMService()

    def _format_phone(self, p: Phone) -> str:
        """格式化手机信息"""
        parts = [f"{p.brand} {p.model}"]
        parts.append(f"价格: {p.price}元")
        if p.processor:
            parts.append(f"处理器: {p.processor}")
        if p.ram:
            parts.append(f"内存: {p.ram}GB")
        if p.storage:
            parts.append(f"存储: {p.storage}GB")
        if p.camera_main:
            parts.append(f"主摄: {p.camera_main}万像素")
        if p.battery:
            parts.append(f"电池: {p.battery}mAh")
        return ", ".join(parts)

    async def recommend(
        self,
        user_need: str,
        phones: List[Phone],
        history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """推荐手机"""
        phones_info = "\n".join([
            f"{i+1}. {self._format_phone(p)}"
            for i, p in enumerate(phones[:5])
        ])
        prompt = RECOMMEND_PROMPT.format(user_need=user_need, phones=phones_info)

        # 构建消息列表，包含历史
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        # 截断消息以满足上下文限制
        original_count = len(messages)
        messages = truncate_messages(
            messages,
            max_tokens=settings.max_context_tokens,
            max_messages=settings.max_context_messages
        )
        if len(messages) < original_count:
            logger.info(f"recommend: truncated {original_count} -> {len(messages)} messages")

        async for chunk in self.llm.chat_stream(messages):
            yield chunk

    async def compare(
        self,
        phones: List[Phone],
        history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """对比手机"""
        phones_info = "\n".join([
            f"{i+1}. {self._format_phone(p)}"
            for i, p in enumerate(phones)
        ])
        prompt = COMPARE_PROMPT.format(phones=phones_info)

        # 构建消息列表，包含历史
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        # 截断消息以满足上下文限制
        original_count = len(messages)
        messages = truncate_messages(
            messages,
            max_tokens=settings.max_context_tokens,
            max_messages=settings.max_context_messages
        )
        if len(messages) < original_count:
            logger.info(f"compare: truncated {original_count} -> {len(messages)} messages")

        async for chunk in self.llm.chat_stream(messages):
            yield chunk
