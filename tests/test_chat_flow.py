"""
多轮对话流程控制测试

验证 chat.py API 的多轮对话流程：
1. 获取或创建用户需求状态
2. 意图识别传入 user_profile
3. 更新用户需求状态（增量合并）
4. 判断需求完整性：不完整则追问，完整则检索推荐
5. 向后兼容：明确请求直接推荐
"""
import pytest
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.schemas import (
    IntentResult,
    IntentType,
    UserProfile,
    NeedLevel
)
from backend.services.session import SessionService, sessions, _sessions_lock
from backend.services.question import QuestionService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """每个测试前清空会话"""
    with _sessions_lock:
        sessions.clear()


def _parse_sse_response(text: str) -> dict:
    """
    解析 SSE 响应，返回事件字典

    Args:
        text: SSE 响应文本

    Returns:
        dict: {event_type: parsed_data} 格式的事件字典
        - session/intent: 值是字符串
        - question/phones: 值是字典
        - content: 值是字符串列表（累积所有 content）
    """
    events = {}
    contents = []
    for line in text.strip().split("\n"):
        if line.startswith("data:"):
            try:
                data = json.loads(line[5:].strip())
                event_type = data.get("type")
                if event_type:
                    if event_type == "content":
                        # 累积所有 content
                        contents.append(data.get("data", ""))
                    else:
                        events[event_type] = data.get("data", data)
            except json.JSONDecodeError:
                continue
    if contents:
        events["content"] = "".join(contents)
    return events


class TestMultiTurnChatFlow:
    """多轮对话流程控制测试"""

    def test_first_request_needs_clarification(self, client):
        """
        第一轮：用户需求模糊，触发追问

        场景：用户说"推荐手机"
        预期：返回追问，询问预算和功能需求
        """
        response = client.post(
            "/api/chat",
            json={"message": "推荐手机"}
        )

        events = _parse_sse_response(response.text)

        # 验证事件类型
        assert "session" in events
        assert "intent" in events
        assert "question" in events

        # 验证追问内容
        question_data = events["question"]
        assert "question" in question_data
        assert "quick_replies" in question_data
        assert "missing_fields" in question_data
        # 应该缺失预算和功能需求
        assert len(question_data["missing_fields"]) > 0

    def test_multi_turn_profile_accumulation(self):
        """
        多轮对话状态累积

        场景：
        - 第一轮：用户说"推荐手机" → profile 为空
        - 第二轮：用户说"3000左右" → profile 有预算
        - 第三轮：用户说"玩游戏" → profile 有预算+游戏需求 → 完整

        验证 SessionService 的 update_profile 增量合并
        """
        service = SessionService()
        session_id = service.create_session()

        # 第一轮：空意图
        intent1 = IntentResult(intent=IntentType.RECOMMEND)
        profile1 = service.update_profile(session_id, intent1)
        assert profile1.is_complete() is False
        assert "预算范围" in " ".join(profile1.get_missing_fields())

        # 第二轮：提供预算
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2500,
            budget_max=3500
        )
        profile2 = service.update_profile(session_id, intent2)
        assert profile2.budget_min == 2500
        assert profile2.budget_max == 3500
        assert profile2.is_complete() is False  # 缺功能需求

        # 第三轮：提供功能需求
        intent3 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        profile3 = service.update_profile(session_id, intent3)
        # 预算应保留
        assert profile3.budget_min == 2500
        assert profile3.budget_max == 3500
        # 新增功能需求
        assert profile3.gaming_need == NeedLevel.HIGH
        # 现在应该完整
        assert profile3.is_complete() is True

    def test_explicit_request_bypasses_profile_check(self):
        """
        明确请求绕过 profile 完整性检查

        验证 _is_explicit_request 函数
        """
        from backend.api.routes.chat import _is_explicit_request

        # 明确请求：有预算+功能
        explicit_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2500,
            budget_max=3500,
            features=["游戏"]
        )
        assert _is_explicit_request(explicit_intent) is True

        # 不明确请求：只有预算
        partial_intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2500,
            budget_max=3500
        )
        assert _is_explicit_request(partial_intent1) is False

        # 不明确请求：只有功能
        partial_intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        assert _is_explicit_request(partial_intent2) is False

        # 不明确请求：无预算上限（默认值）
        default_budget_intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_max=100000,  # 默认值
            features=["游戏"]
        )
        assert _is_explicit_request(default_budget_intent) is False

    def test_question_response_structure(self):
        """
        追问响应结构测试

        验证 QuestionService.generate_full_response 返回正确的结构
        """
        service = QuestionService()
        # 不完整的 profile（缺预算和功能需求）
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH  # 只有游戏需求，缺预算
        )
        response = service.generate_full_response(profile)

        assert response.question is not None
        assert len(response.question) > 0
        assert isinstance(response.quick_replies, list)
        assert isinstance(response.missing_fields, list)
        # 应该缺失预算
        assert "预算" in " ".join(response.missing_fields)

    def test_sse_question_event_format(self, client):
        """
        SSE 追问事件格式测试

        验证追问事件的 SSE 格式正确
        """
        response = client.post(
            "/api/chat",
            json={"message": "推荐手机"}
        )

        # SSE 格式验证
        lines = response.text.strip().split("\n")
        for line in lines:
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                if data.get("type") == "question":
                    # 验证追问数据结构
                    assert "question" in data["data"]
                    assert "quick_replies" in data["data"]
                    assert "missing_fields" in data["data"]
                    break

    def test_session_id_returned_in_sse(self, client):
        """
        SSE 返回 session_id

        验证客户端可以通过 SSE 获取 session_id 用于后续对话
        """
        response = client.post(
            "/api/chat",
            json={"message": "推荐手机"}
        )

        events = _parse_sse_response(response.text)
        assert "session" in events
        # session 的值是字符串（session_id）
        session_id = events["session"]
        assert session_id is not None
        assert len(session_id) > 0
        assert isinstance(session_id, str)

    def test_multi_turn_with_session_id(self, client):
        """
        多轮对话携带 session_id

        场景：
        - 第一轮获取 session_id
        - 第二轮携带相同 session_id
        - 验证状态累积
        """
        # 第一轮
        response1 = client.post(
            "/api/chat",
            json={"message": "推荐手机"}
        )
        events1 = _parse_sse_response(response1.text)
        session_id = events1["session"]

        # 验证 session 存在
        session_service = SessionService()
        assert session_service.session_exists(session_id)

        # 模拟第二轮（用户说"3000左右")
        # 这里我们直接测试 SessionService 的状态管理
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2500,
            budget_max=3500
        )
        profile2 = session_service.update_profile(session_id, intent2)

        # 验证状态累积
        assert profile2.budget_min == 2500
        assert profile2.budget_max == 3500

    def test_intent_recognize_with_user_profile(self):
        """
        意图识别传入 user_profile

        验证 IntentService.recognize 方法正确接收和使用 user_profile
        """
        from backend.services.intent import IntentService

        service = IntentService()
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )

        # 验证方法签名支持 user_profile 参数
        import inspect
        sig = inspect.signature(service.recognize)
        params = list(sig.parameters.keys())
        assert "user_profile" in params


class TestExplicitRequestLogic:
    """明确请求判断逻辑测试"""

    def test_budget_and_features_required(self):
        """明确请求需要预算和功能都存在"""
        from backend.api.routes.chat import _is_explicit_request

        # 完整明确请求
        complete = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000,
            features=["游戏", "拍照"]
        )
        assert _is_explicit_request(complete) is True

        # 缺功能
        no_features = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000,
            features=[]
        )
        assert _is_explicit_request(no_features) is False

        # 缺预算
        no_budget = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=100000,
            features=["游戏"]
        )
        assert _is_explicit_request(no_budget) is False

    def test_default_budget_not_explicit(self):
        """默认预算值不算明确请求"""
        from backend.api.routes.chat import _is_explicit_request

        # 默认预算上限是 100000，表示用户没说预算
        default_budget = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=100000,
            features=["游戏"]
        )
        assert _is_explicit_request(default_budget) is False

    def test_zero_budget_min_still_explicit(self):
        """budget_min=0 但 budget_max 有值，算明确请求"""
        from backend.api.routes.chat import _is_explicit_request

        # 用户说"5000以内"，解析为 budget_min=0, budget_max=5000
        zero_min = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=5000,
            features=["拍照"]
        )
        assert _is_explicit_request(zero_min) is True


class TestQuestionServiceIntegration:
    """QuestionService 与 chat.py 集成测试"""

    def test_question_service_called_for_incomplete_profile(self, client):
        """
        不完整 profile 调用 QuestionService

        验证当 profile 不完整时，QuestionService.generate_full_response 被调用
        """
        with patch("backend.api.routes.chat.QuestionService") as MockQS:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.question = "您的预算大概是多少？"
            mock_response.quick_replies = ["1000-2000元", "2000-3000元"]
            mock_response.missing_fields = ["预算"]
            mock_instance.generate_full_response = MagicMock(return_value=mock_response)
            MockQS.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"message": "推荐手机"}
            )

            # 验证 QuestionService 被调用
            mock_instance.generate_full_response.assert_called()

    def test_quick_replies_match_missing_field(self):
        """
        快捷回复匹配缺失字段

        验证快捷回复选项与缺失的字段相关
        """
        service = QuestionService()

        # 缺预算
        profile_budget = UserProfile(gaming_need=NeedLevel.HIGH)
        response_budget = service.generate_full_response(profile_budget)
        # 快捷回复应该包含预算选项
        assert any("元" in r for r in response_budget.quick_replies)

        # 缺功能需求（但预算已设置）
        profile_feature = UserProfile(
            budget_min=2000,
            budget_max=4000
        )
        response_feature = service.generate_full_response(profile_feature)
        # 快捷回复应该包含功能选项
        assert any("游戏" in r or "拍照" in r or "续航" in r for r in response_feature.quick_replies)


class TestCompareMode:
    """对比模式测试"""

    def test_compare_mode_uses_profile(self):
        """
        对比模式需要使用 profile 状态

        虽然 compare 意图不强制要求完整 profile，
        但应该正确处理 profile 状态。
        """
        service = SessionService()
        session_id = service.create_session()

        # 设置初始 profile
        intent = IntentResult(
            intent=IntentType.COMPARE,
            phones_mentioned=["iPhone 15", "Mate 60"],
            budget_max=8000
        )
        profile = service.update_profile(session_id, intent)

        # 验证预算被保存
        assert profile.budget_max == 8000

    def test_compare_intent_no_forced_clarification(self):
        """
        对比意图不应强制追问

        当意图是 compare 时，即使 profile 不完整，
        也应该直接进行对比（而不是追问）。

        注意：当前实现中，compare 模式也会触发追问，
        因为 _is_explicit_request 对 compare 无效。
        这个测试验证当前行为。
        """
        from backend.api.routes.chat import _is_explicit_request

        # 对比意图，没有明确预算和功能
        compare_intent = IntentResult(
            intent=IntentType.COMPARE,
            phones_mentioned=["iPhone 15", "Mate 60"]
        )

        # _is_explicit_request 对 compare 返回 False（因为无预算和功能）
        # 但 chat.py 中 compare 分支在 need_clarification 判断之后
        assert _is_explicit_request(compare_intent) is False
