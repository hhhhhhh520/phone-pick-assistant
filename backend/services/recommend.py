from backend.services.llm import LLMService, truncate_messages
from backend.models.domain import Phone
from backend.config import get_settings
from typing import List, AsyncGenerator, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()


RECOMMEND_PROMPT = """你是一个专业的手机选购顾问。

用户需求: {user_need}
候选手机列表:
{phones}

请根据用户需求，从上面的候选手机列表中推荐最合适的2-3款手机。
重要：你只能推荐上面列表中的手机，不要推荐列表之外的手机。

## 场景匹配指南
根据用户提到的使用场景，优先关注对应的手机特性：

- **游戏场景**：优先推荐「特性」包含"游戏手机"、"高刷屏"的手机，或「适合」包含"游戏玩家"的手机
- **拍照/摄影场景**：优先推荐「特性」包含"徕卡影像"、"哈苏"、"潜望长焦"等影像标签的手机，或「适合」包含"摄影爱好者"的手机
- **续航场景**：优先推荐电池容量大（5000mAh以上）的手机，关注「特性」中的"快充"标签
- **商务办公**：优先推荐「适合」包含"商务人士"的手机，关注大存储、长续航
- **学生/性价比**：优先推荐「适合」包含"学生"或"性价比"的手机

在推荐理由中，说明该手机如何满足用户提到的具体场景需求。

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
        # 添加特性标签
        if p.features:
            try:
                features = json.loads(p.features) if isinstance(p.features, str) else p.features
                if features:
                    parts.append(f"特性: {', '.join(features)}")
            except (json.JSONDecodeError, TypeError):
                pass
        # 添加适用人群
        if p.suitable_for:
            try:
                suitable = json.loads(p.suitable_for) if isinstance(p.suitable_for, str) else p.suitable_for
                if suitable:
                    parts.append(f"适合: {', '.join(suitable)}")
            except (json.JSONDecodeError, TypeError):
                pass
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
