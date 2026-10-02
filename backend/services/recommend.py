from backend.services.llm import LLMService, truncate_messages
from backend.models.domain import Phone
from backend.config import get_settings
from typing import List, AsyncGenerator, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)
settings = get_settings()


RECOMMEND_SYSTEM_PROMPT = "你是一个专业的手机选购顾问。"

RECOMMEND_PROMPT = """用户需求: {user_need}
候选手机列表:
{phones}

请根据用户需求，从上面的候选手机列表中推荐最合适的2-3款手机。

## 重要约束（违反任何一条都是不合格的输出）

1. 你只能推荐上面列表中的手机，不要推荐列表之外的手机
2. 必须输出完整的手机型号（品牌+型号全称），如 "vivo X200 Pro"、"小米14"，不要只写品牌名如 "vivo"、"小米"
3. 型号名称必须与候选列表中的完全一致，包括空格和大小写
4. **必须引用用户原话**：在推荐理由中，要引用用户在需求中明确提到的具体要求（用引号标注）
5. **【最关键】每款推荐手机必须包含"潜在不足"段落**：如果候选数据中有"缺点:"字段，必须引用其中的内容；如果没有，则根据配置推断至少一个不足。缺少"潜在不足"的推荐是不合格的。

## 输出格式要求

请按以下格式输出：

### 推荐列表
1. **品牌 型号** - 价格元
2. **品牌 型号** - 价格元
3. **品牌 型号** - 价格元

### 用户需求引用
（引用用户原话，说明用户的具体需求是什么，例如：用户提到"拍照要好"、"预算3000左右"等）

### 推荐理由与潜在不足
对于每款推荐手机，必须包含以下两部分（缺一不可）：

**品牌 型号**
- 推荐理由：（说明如何满足用户需求）
- 潜在不足：（必须指出至少一个缺点。优先引用候选数据中的"缺点:"字段；若无则根据配置推断，如：重量较大、续航一般、缺少长焦等。不可省略此项。）

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

COMPARE_SYSTEM_PROMPT = "你是一个手机参数对比专家。"

COMPARE_PROMPT = """用户想对比以下手机:
{phones}

请从以下维度对比:
1. 性能(处理器、内存)
2. 拍照(摄像头配置)
3. 续航(电池、充电)
4. 价格

用简洁语言总结差异，给出选择建议。
"""


def _format_storage(storage: int | None) -> str | None:
    """存储展示：GB 口径整数，≥1024 整数倍转 TB（1TB 曾被截断为 1，数据已修为 1024，ISSUE-048）"""
    if not storage:
        return None
    if storage >= 1024 and storage % 1024 == 0:
        return f"{storage // 1024}TB"
    return f"{storage}GB"


class RecommendService:
    def __init__(self):
        self.llm = LLMService()

    def _format_phone(self, p: Phone) -> str:
        """格式化手机信息"""
        parts = [p.display_name]
        parts.append(f"价格: {p.price}元")
        if p.processor:
            parts.append(f"处理器: {p.processor}")
        if p.ram:
            parts.append(f"内存: {p.ram}GB")
        storage_display = _format_storage(p.storage)
        if storage_display:
            parts.append(f"存储: {storage_display}")
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
        # 添加优点
        if p.pros:
            try:
                pros = json.loads(p.pros) if isinstance(p.pros, str) else p.pros
                if pros:
                    parts.append(f"优点: {', '.join(pros)}")
            except (json.JSONDecodeError, TypeError):
                pass
        # 添加缺点
        if p.cons:
            try:
                cons = json.loads(p.cons) if isinstance(p.cons, str) else p.cons
                if cons:
                    parts.append(f"缺点: {', '.join(cons)}")
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
        # 转义用户输入中的花括号，防止 str.format() KeyError DoS
        safe_user_need = user_need.replace("{", "{{").replace("}", "}}")
        prompt = RECOMMEND_PROMPT.format(user_need=safe_user_need, phones=phones_info)

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

        # 收集完整输出，检查是否包含缺点披露
        full_content = ""
        async for chunk in self.llm.chat_stream(messages, system_prompt=RECOMMEND_SYSTEM_PROMPT):
            full_content += chunk
            yield chunk

        # 后处理：如果 LLM 输出缺少缺点，自动补充
        cons_keywords = ['不足', '缺点', '局限', '短板', '注意', '不过', '遗憾']
        has_cons = any(kw in full_content for kw in cons_keywords)
        logger.info(f"Post-process: content_len={len(full_content)}, has_cons={has_cons}")
        if not has_cons:
            # 从推荐的手机中提取 cons 数据
            cons_lines = []
            for p in phones[:5]:
                if p.cons:
                    try:
                        cons_list = json.loads(p.cons) if isinstance(p.cons, str) else p.cons
                        if cons_list:
                            cons_lines.append(f"- **{p.display_name}**：{'、'.join(cons_list[:3])}")
                    except (json.JSONDecodeError, TypeError):
                        pass
            if cons_lines:
                cons_output = "\n\n### 潜在不足\n" + "\n".join(cons_lines)
                logger.info(f"Post-process: adding cons for {len(cons_lines)} phones")
                yield cons_output
            else:
                logger.info("Post-process: no cons data available")

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

        async for chunk in self.llm.chat_stream(messages, system_prompt=COMPARE_SYSTEM_PROMPT):
            yield chunk
