"""
共享测试配置和 fixtures
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.schemas import IntentResult, IntentType
from backend.models.domain import Phone
from backend.services.session import sessions, _sessions_lock


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """每个测试前清空会话"""
    with _sessions_lock:
        sessions.clear()


def _parse_sse_response(text: str) -> dict:
    """解析 SSE 响应，返回事件字典"""
    events = {}
    contents = []
    for line in text.strip().split("\n"):
        if line.startswith("data:"):
            try:
                data = json.loads(line[5:].strip())
                event_type = data.get("type")
                if event_type:
                    if event_type == "content":
                        contents.append(data.get("data", ""))
                    else:
                        events[event_type] = data.get("data", data)
            except json.JSONDecodeError:
                continue
    if contents:
        events["content"] = "".join(contents)
    return events


def _make_phone(brand="小米", model="小米14", price=3999, **kwargs):
    """创建测试用 Phone 对象"""
    p = Phone(
        brand=brand, model=model, price=price,
        processor="骁龙8 Gen3", ram=8, storage=256,
        camera_main=5000, battery=4610,
        features='["游戏", "旗舰"]',
        suitable_for='["游戏玩家"]',
        pros='["性能强", "拍照好"]',
        cons='["续航一般", "重量较重"]',
    )
    for k, v in kwargs.items():
        setattr(p, k, v)
    return p


def _make_intent(intent_type=IntentType.RECOMMEND, budget_max=5000, features=None, phones_mentioned=None):
    """创建测试用 IntentResult"""
    return IntentResult(
        intent=intent_type,
        budget_min=0,
        budget_max=budget_max,
        brands=[],
        features=features or ["游戏"],
        no_need_features=[],
        phones_mentioned=phones_mentioned or [],
        need_clarification=False,
        reset_profile=False,
    )
