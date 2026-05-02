from backend.services.llm import LLMService, truncate_messages
from backend.models.schemas import IntentResult, IntentType
import json
import logging
import re

logger = logging.getLogger(__name__)

INTENT_PROMPT = """你是一个手机选购助手。分析用户意图并提取关键信息。

{history_context}
用户输入: "{user_message}"

返回JSON格式(不要有其他内容):
{{
  "intent": "recommend或compare或filter",
  "budget_min": 0,
  "budget_max": 10000,
  "brands": ["品牌列表"],
  "features": ["功能需求列表"],
  "phones_mentioned": ["提到的手机型号"]
}}

intent说明:
- recommend: 用户想要推荐手机
- compare: 用户想对比两款手机
- filter: 用户想按条件筛选

预算提取规则（重要）:
- "三千价位" → budget_min=2500, budget_max=3500
- "五千价位" → budget_min=4500, budget_max=5500
- "一万以内" → budget_min=0, budget_max=10000
- 如果用户说具体价格如"3000元左右"，设置 ±500 的范围
- 如果没有明确预算，保持 budget_min=0, budget_max=100000

多轮对话规则（重要）:
- 如果用户追问"便宜点的/贵点的"，需要参考历史上下文调整预算
- "便宜点的" → 在原预算基础上降低1000-2000元
- "贵点的" → 在原预算基础上提高1000-2000元
- 如果历史上下文提到过手机型号，用户追问时可能想对比或了解同系列
"""


class IntentService:
    def __init__(self):
        self.llm = LLMService()

    def _fallback_intent_recognition(self, user_message: str) -> IntentResult:
        """基于规则的降级意图识别"""
        message_lower = user_message.lower()

        # 检测对比意图
        if "对比" in message_lower or "比较" in message_lower or "哪个好" in message_lower:
            return IntentResult(intent=IntentType.COMPARE)

        # 检测筛选意图
        if "筛选" in message_lower or "过滤" in message_lower or "只看" in message_lower:
            return IntentResult(intent=IntentType.FILTER)

        # 默认推荐意图
        return IntentResult(intent=IntentType.RECOMMEND)

    def _extract_json_from_response(self, response: str) -> dict:
        """从LLM响应中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON块
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    async def recognize(self, user_message: str, history: list = None) -> IntentResult:
        """识别用户意图

        Args:
            user_message: 用户当前输入
            history: 历史消息列表，格式 [{"role": "user/assistant", "content": "..."}]
        """
        # 构建历史上下文
        history_context = ""
        if history and len(history) > 0:
            # 使用统一的截断方法处理历史消息
            truncated_history = truncate_messages(history, max_messages=6)
            history_lines = []
            for msg in truncated_history:
                role = "用户" if msg["role"] == "user" else "助手"
                history_lines.append(f"{role}: {msg['content']}")
            history_context = "历史对话:\n" + "\n".join(history_lines) + "\n\n"

        prompt = INTENT_PROMPT.format(user_message=user_message, history_context=history_context)
        response = await self.llm.chat([{"role": "user", "content": prompt}])

        try:
            data = self._extract_json_from_response(response)
            if data is None:
                logger.warning(f"Intent JSON parse failed, raw response: {response[:200]}")
                return self._fallback_intent_recognition(user_message)

            return IntentResult(
                intent=IntentType(data.get("intent", "recommend")),
                budget_min=data.get("budget_min", 0),
                budget_max=data.get("budget_max", 100000),
                brands=data.get("brands", []),
                features=data.get("features", []),
                phones_mentioned=data.get("phones_mentioned", [])
            )
        except ValueError as e:
            logger.warning(f"Intent recognition error: {e}, raw response: {response[:200]}")
            return self._fallback_intent_recognition(user_message)