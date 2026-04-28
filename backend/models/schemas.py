from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class IntentType(str, Enum):
    RECOMMEND = "recommend"
    COMPARE = "compare"
    FILTER = "filter"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


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
