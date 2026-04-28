from backend.services.llm import LLMService
from backend.models.schemas import IntentResult, IntentType
import json

INTENT_PROMPT = """你是一个手机选购助手。分析用户意图并提取关键信息。

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
"""


class IntentService:
    def __init__(self):
        self.llm = LLMService()

    async def recognize(self, user_message: str) -> IntentResult:
        """识别用户意图"""
        prompt = INTENT_PROMPT.format(user_message=user_message)
        response = await self.llm.chat([{"role": "user", "content": prompt}])

        try:
            data = json.loads(response)
            return IntentResult(
                intent=IntentType(data.get("intent", "recommend")),
                budget_min=data.get("budget_min", 0),
                budget_max=data.get("budget_max", 100000),
                brands=data.get("brands", []),
                features=data.get("features", []),
                phones_mentioned=data.get("phones_mentioned", [])
            )
        except (json.JSONDecodeError, ValueError):
            return IntentResult(intent=IntentType.RECOMMEND)
