"""
补充后端单元测试

测试覆盖：
1. 需求完整性判断边界情况
2. 追问生成边界情况
3. 状态合并逻辑
4. 快捷回复解析
5. SessionService 并发会话隔离
6. UserProfile 边界情况
7. QuestionService 边界情况
"""
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch, AsyncMock
from backend.models.schemas import (
    UserProfile,
    NeedLevel,
    IntentResult,
    IntentType
)
from backend.services.session import SessionService, sessions, _sessions_lock
from backend.services.need_analysis import NeedAnalysisService, AnalysisResult
from backend.services.question import QuestionService, QuestionResponse


class TestUserProfileBoundaryCases:
    """UserProfile 边界情况测试"""

    def test_budget_min_only(self):
        """只有预算下限"""
        profile = UserProfile(budget_min=3000)
        # 应该算有预算
        assert profile.budget_min is not None
        # 加一个功能需求就完整
        profile2 = UserProfile(budget_min=3000, gaming_need=NeedLevel.HIGH)
        assert profile2.is_complete() is True

    def test_budget_max_only(self):
        """只有预算上限"""
        profile = UserProfile(budget_max=5000)
        # 应该算有预算
        assert profile.budget_max is not None
        # 加一个功能需求就完整
        profile2 = UserProfile(budget_max=5000, camera_need=NeedLevel.MEDIUM)
        assert profile2.is_complete() is True

    def test_budget_same_min_max(self):
        """预算上下限相同"""
        profile = UserProfile(budget_min=3000, budget_max=3000)
        assert profile.budget_min == 3000
        assert profile.budget_max == 3000
        # 加功能需求完整
        profile2 = UserProfile(budget_min=3000, budget_max=3000, gaming_need=NeedLevel.LOW)
        assert profile2.is_complete() is True

    def test_budget_reversed(self):
        """预算下限大于上限（异常数据）"""
        # 数据模型不阻止这种情况，但逻辑上不合理
        profile = UserProfile(budget_min=5000, budget_max=3000)
        assert profile.budget_min > profile.budget_max

    def test_brand_preference_empty_list_vs_none(self):
        """空品牌偏好列表 vs None"""
        profile_none = UserProfile(gaming_need=NeedLevel.HIGH, budget_min=2000)
        profile_empty = UserProfile(gaming_need=NeedLevel.HIGH, budget_min=2000, brand_preference=[])

        # None 表示未设置，空列表表示设置了但没有偏好
        assert profile_none.brand_preference is None
        assert profile_empty.brand_preference == []
        # 两者的完整性应该相同（品牌是可选的）
        assert profile_none.is_complete() is True
        assert profile_empty.is_complete() is True

    def test_brand_preference_single_item(self):
        """单一品牌偏好"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH,
            brand_preference=["小米"]
        )
        assert len(profile.brand_preference) == 1
        assert profile.is_complete() is True

    def test_brand_preference_multiple_items(self):
        """多品牌偏好"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH,
            brand_preference=["小米", "华为", "苹果", "OPPO"]
        )
        assert len(profile.brand_preference) == 4
        assert profile.is_complete() is True

    def test_need_level_all_types(self):
        """所有需求等级"""
        for level in [NeedLevel.HIGH, NeedLevel.MEDIUM, NeedLevel.LOW]:
            profile = UserProfile(
                budget_min=2000,
                gaming_need=level
            )
            assert profile.gaming_need == level
            assert profile.is_complete() is True

    def test_all_feature_needs_set(self):
        """所有功能需求都设置"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            battery_need=NeedLevel.LOW
        )
        assert profile.is_complete() is True
        assert len(profile.get_missing_fields()) == 0

    def test_two_feature_needs(self):
        """两个功能需求"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM
        )
        assert profile.is_complete() is True
        assert len(profile.get_missing_fields()) == 0


class TestNeedAnalysisBoundaryCases:
    """NeedAnalysisService 边界情况测试"""

    @pytest.fixture
    def service(self):
        return NeedAnalysisService()

    def test_analyze_with_negative_budget(self, service):
        """负数预算（异常数据）"""
        profile = UserProfile(budget_min=-1000, gaming_need=NeedLevel.HIGH)
        # 模型不会阻止负数，但逻辑上不合理
        result = service.analyze(profile)
        # 有预算边界，有功能需求，应该完整
        assert result.is_complete is True

    def test_analyze_with_zero_budget(self, service):
        """零预算"""
        profile = UserProfile(budget_min=0, budget_max=0, gaming_need=NeedLevel.HIGH)
        result = service.analyze(profile)
        # 有预算边界，有功能需求，应该完整
        assert result.is_complete is True

    def test_analyze_with_very_large_budget(self, service):
        """非常大的预算"""
        profile = UserProfile(budget_max=999999, gaming_need=NeedLevel.HIGH)
        result = service.analyze(profile)
        assert result.is_complete is True

    def test_generate_question_with_empty_missing_fields(self, service):
        """没有缺失字段时生成问题"""
        question = service._generate_question([])
        assert question is None

    def test_generate_question_with_unknown_missing_field(self, service):
        """未知缺失字段生成问题"""
        # 使用不在模板中的字段
        question = service._generate_question(["未知字段"])
        # 应使用默认模板
        assert question is not None


class TestQuestionServiceBoundaryCases:
    """QuestionService 边界情况测试"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_generate_question_with_invalid_field(self, service):
        """无效字段名生成问题"""
        # 当传入完全无效的字段名时，无法匹配任何已知字段
        # 当前实现在 field_names 为空时会抛出 IndexError
        # 这是一个边界情况，测试当前行为
        with pytest.raises(IndexError):
            service.generate_question(["invalid_field_xyz"])

    def test_generate_question_with_duplicate_fields(self, service):
        """重复字段名"""
        question = service.generate_question(["budget", "budget", "gaming_need"])
        # 去重后应该只处理一个 budget
        assert question is not None
        # 应包含预算或游戏相关内容
        has_budget = "预算" in question or "钱" in question
        has_gaming = "游戏" in question
        assert has_budget or has_gaming

    def test_generate_question_with_unordered_fields(self, service):
        """字段顺序不正确"""
        # 传入顺序不按优先级
        question = service.generate_question(["brand_preference", "budget"])
        # 应该按优先级排序后生成
        assert "预算" in question or "品牌" in question

    def test_generate_quick_replies_for_invalid_field(self, service):
        """无效字段的快捷回复"""
        replies = service.generate_quick_replies("invalid_field")
        assert replies == []

    def test_generate_full_response_with_null_profile_fields(self, service):
        """部分字段为 None 的画像"""
        profile = UserProfile(budget_min=None, budget_max=None)
        response = service.generate_full_response(profile)
        assert response.question != ""
        assert "预算" in response.missing_fields

    def test_get_missing_field_names_with_partial_budget(self, service):
        """部分预算边界"""
        # 只设置上限
        profile = UserProfile(budget_max=5000)
        missing = service._get_missing_field_names(profile)
        assert "budget" not in missing

        # 只设置下限
        profile2 = UserProfile(budget_min=2000)
        missing2 = service._get_missing_field_names(profile2)
        assert "budget" not in missing2

    def test_quick_replies_content_validation(self, service):
        """快捷回复内容有效性"""
        # 预算快捷回复应该包含价格信息
        budget_replies = service.generate_quick_replies("budget")
        for reply in budget_replies:
            assert "元" in reply or "以上" in reply

        # 游戏快捷回复应该包含游戏相关内容
        gaming_replies = service.generate_quick_replies("gaming_need")
        for reply in gaming_replies:
            assert len(reply) > 0

    def test_field_priority_unknown_field(self, service):
        """未知字段优先级"""
        priority = service.get_field_priority("unknown_field")
        # 应该大于已知字段的最高优先级
        assert priority > 4


class TestSessionServiceConcurrencyIsolation:
    """SessionService 并发会话隔离测试"""

    def setup_method(self):
        """每个测试前清空会话"""
        with _sessions_lock:
            sessions.clear()

    def test_concurrent_sessions_isolated(self):
        """并发会话之间隔离"""
        service = SessionService()
        session_ids = []

        # 创建多个会话
        for i in range(10):
            sid = service.create_session()
            session_ids.append(sid)

        # 并发更新不同会话的状态
        def update_session(i):
            sid = session_ids[i]
            intent = IntentResult(
                intent=IntentType.RECOMMEND,
                budget_min=1000 + i * 100,
                budget_max=2000 + i * 100
            )
            service.update_profile(sid, intent)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_session, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()

        # 验证每个会话的状态独立
        for i, sid in enumerate(session_ids):
            profile = service.get_profile(sid)
            assert profile.budget_min == 1000 + i * 100
            assert profile.budget_max == 2000 + i * 100

    def test_session_does_not_interfere_other_sessions(self):
        """一个会话的操作不影响其他会话"""
        service = SessionService()

        # 创建两个会话
        sid1 = service.create_session()
        sid2 = service.create_session()

        # 会话1设置预算
        intent1 = IntentResult(intent=IntentType.RECOMMEND, budget_min=2000, budget_max=4000)
        service.update_profile(sid1, intent1)

        # 会话2设置不同的预算
        intent2 = IntentResult(intent=IntentType.RECOMMEND, budget_min=5000, budget_max=8000)
        service.update_profile(sid2, intent2)

        # 验证会话1的状态不变
        profile1 = service.get_profile(sid1)
        assert profile1.budget_min == 2000
        assert profile1.budget_max == 4000

        # 验证会话2的状态
        profile2 = service.get_profile(sid2)
        assert profile2.budget_min == 5000
        assert profile2.budget_max == 8000

    def test_message_isolation_between_sessions(self):
        """消息隔离"""
        service = SessionService()

        sid1 = service.create_session()
        sid2 = service.create_session()

        # 会话1添加消息
        service.add_message(sid1, "user", "message for session 1")
        service.add_message(sid1, "assistant", "response for session 1")

        # 会话2添加不同消息
        service.add_message(sid2, "user", "message for session 2")

        # 验证消息隔离
        messages1 = service.get_messages(sid1)
        messages2 = service.get_messages(sid2)

        assert len(messages1) == 2
        assert len(messages2) == 1
        assert messages1[0]["content"] == "message for session 1"
        assert messages2[0]["content"] == "message for session 2"

    def test_nonexistent_session_returns_none(self):
        """不存在的会话返回 None"""
        service = SessionService()

        # 获取不存在的会话
        messages = service.get_session("nonexistent-id")
        assert messages is None

        profile = service.get_profile("nonexistent-id")
        assert profile is None

    def test_update_profile_creates_session_if_not_exists(self):
        """更新状态时自动创建会话"""
        service = SessionService()

        # 使用不存在的 session_id
        fake_sid = "fake-session-id-12345"
        intent = IntentResult(intent=IntentType.RECOMMEND, budget_min=3000)
        profile = service.update_profile(fake_sid, intent)

        # 应该自动创建了会话
        assert service.session_exists(fake_sid)
        assert profile.budget_min == 3000

    def test_add_message_creates_session_if_not_exists(self):
        """添加消息时自动创建会话"""
        service = SessionService()

        fake_sid = "another-fake-session-id"
        service.add_message(fake_sid, "user", "test message")

        # 应该自动创建了会话
        assert service.session_exists(fake_sid)
        messages = service.get_messages(fake_sid)
        assert len(messages) == 1


class TestIntentResultUpdateProfile:
    """IntentResult 与 UserProfile 状态合并逻辑测试"""

    def test_merge_preserves_all_existing_values(self):
        """合并保留所有现有值"""
        # 原画像有多个值
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            brand_preference=["小米"]
        )

        # 新意图只有一个新字段
        intent = IntentResult(intent=IntentType.RECOMMEND, features=["续航"])
        updated = profile.update_from_intent(intent)

        # 所有原值保留
        assert updated.budget_min == 2000
        assert updated.budget_max == 4000
        assert updated.gaming_need == NeedLevel.HIGH
        assert updated.camera_need == NeedLevel.MEDIUM
        assert updated.brand_preference == ["小米"]
        # 新值添加
        assert updated.battery_need == NeedLevel.HIGH

    def test_merge_overrides_budget(self):
        """合并覆盖预算"""
        profile = UserProfile(budget_min=2000, budget_max=4000)

        # 新意图有新预算
        intent = IntentResult(intent=IntentType.RECOMMEND, budget_min=3000, budget_max=5000)
        updated = profile.update_from_intent(intent)

        # 预算被覆盖
        assert updated.budget_min == 3000
        assert updated.budget_max == 5000

    def test_merge_adds_to_brand_preference(self):
        """合并添加到品牌偏好"""
        profile = UserProfile(brand_preference=["小米"])

        intent = IntentResult(intent=IntentType.RECOMMEND, brands=["华为"])
        updated = profile.update_from_intent(intent)

        # 品牌合并，去重
        assert "小米" in updated.brand_preference
        assert "华为" in updated.brand_preference
        assert len(updated.brand_preference) == 2

    def test_features_with_multiple_keywords(self):
        """多个关键词的 features"""
        profile = UserProfile()

        intent = IntentResult(intent=IntentType.RECOMMEND, features=["游戏", "拍照", "续航"])
        updated = profile.update_from_intent(intent)

        # 所有需求都被识别
        assert updated.gaming_need == NeedLevel.HIGH
        assert updated.camera_need == NeedLevel.HIGH
        assert updated.battery_need == NeedLevel.HIGH

    def test_features_with_mixed_keywords(self):
        """混合关键词的 features"""
        profile = UserProfile()

        intent = IntentResult(intent=IntentType.RECOMMEND, features=["打游戏", "要拍照好", "快充"])
        updated = profile.update_from_intent(intent)

        # 关键词被识别（包含"游戏"、"拍照"、"快充"）
        assert updated.gaming_need == NeedLevel.HIGH
        assert updated.camera_need == NeedLevel.HIGH
        # 快充关联 MEDIUM 续航需求
        assert updated.battery_need == NeedLevel.MEDIUM

    def test_features_with_unknown_keywords(self):
        """未知关键词的 features"""
        profile = UserProfile()

        intent = IntentResult(intent=IntentType.RECOMMEND, features=["外观好看", "手感好"])
        updated = profile.update_from_intent(intent)

        # 未知关键词不影响功能需求
        assert updated.gaming_need is None
        assert updated.camera_need is None
        assert updated.battery_need is None

    def test_empty_features_list(self):
        """空 features 列表"""
        profile = UserProfile()

        intent = IntentResult(intent=IntentType.RECOMMEND, features=[])
        updated = profile.update_from_intent(intent)

        # 不设置任何功能需求
        assert updated.gaming_need is None
        assert updated.camera_need is None
        assert updated.battery_need is None


class TestQuickReplyParsing:
    """快捷回复解析测试"""

    @pytest.fixture
    def service(self):
        return QuestionService()

    def test_budget_quick_reply_formats(self, service):
        """预算快捷回复格式"""
        replies = service.generate_quick_replies("budget")
        # 验证格式正确
        assert len(replies) == 4
        # 应该是价格范围格式
        for reply in replies:
            # 格式应该包含数字和"元"或"以上"
            assert any(c.isdigit() for c in reply) or "以上" in reply

    def test_gaming_quick_reply_formats(self, service):
        """游戏需求快捷回复格式"""
        replies = service.generate_quick_replies("gaming_need")
        assert len(replies) == 4
        # 应该包含游戏相关选项
        valid_options = ["不玩游戏", "王者/吃鸡", "原神/崩铁", "重度游戏"]
        for reply in replies:
            assert reply in valid_options

    def test_camera_quick_reply_formats(self, service):
        """拍照需求快捷回复格式"""
        replies = service.generate_quick_replies("camera_need")
        assert len(replies) == 4
        valid_options = ["不太拍照", "日常记录", "人像/风景", "专业摄影"]
        for reply in replies:
            assert reply in valid_options

    def test_battery_quick_reply_formats(self, service):
        """续航需求快捷回复格式"""
        replies = service.generate_quick_replies("battery_need")
        assert len(replies) == 3
        valid_options = ["一天一充就行", "希望两天一充", "重度使用"]
        for reply in replies:
            assert reply in valid_options

    def test_brand_quick_reply_formats(self, service):
        """品牌偏好快捷回复格式"""
        replies = service.generate_quick_replies("brand_preference")
        assert len(replies) == 5
        # 应该包含主要品牌
        assert "小米" in replies
        assert "华为" in replies
        assert "苹果" in replies
        assert "OPPO/vivo" in replies
        assert "都可以" in replies

    def test_quick_replies_consistency(self, service):
        """快捷回复与问题一致性"""
        # 缺预算时，问题和快捷回复都应该与预算相关
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        response = service.generate_full_response(profile)

        # 问题应该问预算
        assert "预算" in response.question or "钱" in response.question
        # 快捷回复应该是预算选项
        assert any("元" in r for r in response.quick_replies)


class TestAnalysisResultEdgeCases:
    """AnalysisResult 边界情况测试"""

    def test_to_dict_with_none_question(self):
        """suggested_question 为 None"""
        result = AnalysisResult(
            is_complete=True,
            missing_fields=[],
            suggested_question=None
        )
        d = result.to_dict()
        assert d["suggested_question"] is None

    def test_to_dict_with_empty_missing_fields(self):
        """missing_fields 为空"""
        result = AnalysisResult(
            is_complete=True,
            missing_fields=[],
            suggested_question=None
        )
        d = result.to_dict()
        assert d["missing_fields"] == []

    def test_to_dict_with_all_fields(self):
        """所有字段都有值"""
        result = AnalysisResult(
            is_complete=False,
            missing_fields=["预算", "功能"],
            suggested_question="请告诉我您的预算"
        )
        d = result.to_dict()
        assert d["is_complete"] is False
        assert d["missing_fields"] == ["预算", "功能"]
        assert d["suggested_question"] == "请告诉我您的预算"

    def test_equality_with_different_types(self):
        """与不同类型比较"""
        result = AnalysisResult(is_complete=True, missing_fields=[], suggested_question=None)
        assert result != "not an AnalysisResult"
        assert result != 123
        assert result != {"is_complete": True}

    def test_repr_format(self):
        """repr 格式"""
        result = AnalysisResult(
            is_complete=False,
            missing_fields=["预算"],
            suggested_question="预算多少？"
        )
        repr_str = repr(result)
        assert "AnalysisResult" in repr_str
        assert "is_complete=False" in repr_str
        assert "missing_fields" in repr_str
        assert "suggested_question" in repr_str


class TestQuestionResponseEdgeCases:
    """QuestionResponse 边界情况测试"""

    def test_response_with_empty_strings(self):
        """空字符串问题"""
        response = QuestionResponse(
            question="",
            quick_replies=[""],
            missing_fields=[]
        )
        assert response.question == ""
        assert response.quick_replies == [""]

    def test_response_with_long_question(self):
        """长问题"""
        long_question = "请告诉我您的预算范围、游戏需求、拍照需求、续航需求和品牌偏好。" * 5
        response = QuestionResponse(
            question=long_question,
            quick_replies=["选项1"],
            missing_fields=["字段1"]
        )
        assert response.question == long_question

    def test_response_with_many_quick_replies(self):
        """多个快捷回复"""
        many_replies = [f"选项{i}" for i in range(20)]
        response = QuestionResponse(
            question="问题",
            quick_replies=many_replies,
            missing_fields=["字段"]
        )
        assert len(response.quick_replies) == 20

    def test_response_model_validation(self):
        """模型验证"""
        # 正常创建
        response = QuestionResponse(
            question="问题",
            quick_replies=["选项A", "选项B"],
            missing_fields=["预算", "功能"]
        )
        assert isinstance(response.question, str)
        assert isinstance(response.quick_replies, list)
        assert isinstance(response.missing_fields, list)