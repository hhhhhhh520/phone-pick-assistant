from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class IntentType(str, Enum):
    RECOMMEND = "recommend"
    COMPARE = "compare"
    FILTER = "filter"


class ChatRequest(BaseModel):
    message: str = Field(
        max_length=2000,
        description="用户输入消息",
        examples=["推荐一款3000元左右的手机"]
    )
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """验证消息长度和非空"""
        if not v or not v.strip():
            raise ValueError("消息不能为空")
        # 注意：Pydantic max_length 已处理长度限制
        # 这里可以添加额外的内容验证
        return v.strip()


class PhoneBrief(BaseModel):
    id: int
    brand: str
    model: str
    price: int


class PhoneListResponse(BaseModel):
    phones: List[PhoneBrief]
    total: int


class IntentResult(BaseModel):
    intent: IntentType
    budget_min: Optional[int] = 0
    budget_max: Optional[int] = 100000
    brands: Optional[List[str]] = []
    features: Optional[List[str]] = []
    phones_mentioned: Optional[List[str]] = []
