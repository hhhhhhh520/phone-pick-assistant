from backend.services.llm import LLMService
from backend.models.domain import Phone
from backend.models.schemas import IntentType
from typing import List, AsyncGenerator, Dict, Optional

RECOMMEND_PROMPT = """你是一个专业的手机选购顾问。

用户需求: {user_need}
候选手机: {phones}

请根据用户需求推荐最合适的2-3款手机，说明推荐理由。
用简洁自然的语言回答，不要过于正式。
"""

COMPARE_PROMPT = """你是一个手机参数对比专家。

用户想对比: {phones}

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

    async def recommend(
        self,
        user_need: str,
        phones: List[Phone],
        history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """推荐手机"""
        phones_info = "\n".join([
            f"- {p.brand} {p.model}: {p.price}元, {p.processor}, {p.ram}GB内存, {p.camera_main}万像素主摄"
            for p in phones[:5]
        ])
        prompt = RECOMMEND_PROMPT.format(user_need=user_need, phones=phones_info)

        # 构建消息列表，包含历史
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        async for chunk in self.llm.chat_stream(messages):
            yield chunk

    async def compare(
        self,
        phones: List[Phone],
        history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """对比手机"""
        phones_info = "\n".join([
            f"- {p.brand} {p.model}: {p.price}元, {p.processor}, {p.ram}GB内存, {p.camera_main}万像素, {p.battery}mAh电池"
            for p in phones
        ])
        prompt = COMPARE_PROMPT.format(phones=phones_info)

        # 构建消息列表，包含历史
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        async for chunk in self.llm.chat_stream(messages):
            yield chunk
