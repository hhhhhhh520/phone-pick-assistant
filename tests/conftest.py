"""
共享测试配置和 fixtures
"""
import pytest
import json
import sys
import os
from contextlib import contextmanager
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.schemas import IntentResult, IntentType
from backend.models.domain import Phone
from backend.services.llm import LLMError
from backend.services.session import sessions, _sessions_lock


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """每个测试前清空会话"""
    with _sessions_lock:
        sessions.clear()


@pytest.fixture(autouse=True)
def offline_llm():
    """测试离线隔离：阻断 LLMService 的真实网络调用

    LLMService.chat_stream 是全项目唯一的 LLM 网络入口（intent/recommend/compare
    都经它调用 DeepSeek）。不 mock 时测试套件依赖 DeepSeek 账户余额：
    2026-09-06 曾因账户 402 Insufficient Balance 导致 19 个测试失败。
    抛 LLMError 后，上层（intent 规则兜底 / chat.py SSE error 事件）按
    生产降级路径处理，测试行为确定且离线。
    需要自定义 chat_stream 行为的测试可在测试内部再 patch（内层覆盖外层）。
    """
    with patch("backend.services.llm.LLMService.chat_stream",
               side_effect=LLMError("LLM offline (test isolation)")):
        yield


@pytest.fixture(autouse=True)
def clear_di_overrides():
    """每个测试后清理 FastAPI 依赖覆盖，避免 mock 泄漏到其他测试"""
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """每个测试前后重置限流器

    全量套件在数秒内跑完，所有测试共享同一个 60s 限流窗口，
    累计请求数会超过 20/min 触发 429，造成顺序依赖的偶发失败。
    """
    from backend.api.routes import chat as chat_route
    from backend.api.routes import phones as phones_route
    from backend import main as main_module
    app_limiter = main_module.limiter
    chat_limiter = chat_route.limiter
    phones_limiter = phones_route.limiter
    app_limiter.reset()
    chat_limiter.reset()
    phones_limiter.reset()
    yield
    app_limiter.reset()
    chat_limiter.reset()
    phones_limiter.reset()


@contextmanager
def override_chat_services(intent=None, recommend=None):
    """覆盖 chat 路由的 DI 服务

    chat.py 的 IntentService/RecommendService 来自 api/dependencies.py 的单例 DI，
    patch("backend.api.routes.chat.IntentService") 这类模块级 patch 不生效
    （路由用的是 dependencies 里的单例，不是 chat 模块里的名字）。
    用 FastAPI 官方的 dependency_overrides 才能真正替换。
    RetrievalService 在路由内联构造，patch chat.RetrievalService 有效，无需覆盖。
    """
    from backend.api.dependencies import get_intent_service, get_recommend_service
    if intent is not None:
        app.dependency_overrides[get_intent_service] = lambda: intent
    if recommend is not None:
        app.dependency_overrides[get_recommend_service] = lambda: recommend
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_intent_service, None)
        app.dependency_overrides.pop(get_recommend_service, None)


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
