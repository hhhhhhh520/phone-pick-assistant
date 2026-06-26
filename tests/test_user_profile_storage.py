"""
用户需求状态存储测试 - 验证 SessionService 的 profile 功能
"""
import pytest
from backend.services.session import SessionService, Session, SessionData, sessions, _sessions_lock
from backend.models.schemas import UserProfile, IntentResult, IntentType, NeedLevel


class TestUserProfileStorage:
    """用户需求状态存储测试"""

    def setup_method(self):
        """每个测试前清空会话"""
        with _sessions_lock:
            sessions.clear()

    def test_get_profile_no_session(self):
        """测试获取不存在会话的 profile"""
        service = SessionService()
        result = service.get_profile("non-existent-session")
        assert result is None

    def test_get_profile_empty_session(self):
        """测试获取空会话的 profile"""
        service = SessionService()
        session_id = service.create_session()
        result = service.get_profile(session_id)
        assert result is None

    def test_save_and_get_profile(self):
        """测试保存和获取 profile"""
        service = SessionService()
        session_id = service.create_session()

        profile = UserProfile(
            budget_min=1000,
            budget_max=3000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM
        )

        service.save_profile(session_id, profile)

        result = service.get_profile(session_id)
        assert result is not None
        assert result.budget_min == 1000
        assert result.budget_max == 3000
        assert result.gaming_need == NeedLevel.HIGH
        assert result.camera_need == NeedLevel.MEDIUM

    def test_save_profile_creates_session_if_not_exists(self):
        """测试保存 profile 时如果会话不存在会自动创建"""
        service = SessionService()
        non_existent_session = "non-existent-session-id"

        profile = UserProfile(budget_max=5000)
        service.save_profile(non_existent_session, profile)

        # 验证会话被创建
        assert service.session_exists(non_existent_session)
        result = service.get_profile(non_existent_session)
        assert result is not None
        assert result.budget_max == 5000

    def test_update_profile_new_session(self):
        """测试在新会话中更新 profile"""
        service = SessionService()
        session_id = service.create_session()

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000,
            features=["游戏", "拍照"]
        )

        result = service.update_profile(session_id, intent)

        assert result.budget_min == 2000
        assert result.budget_max == 4000
        assert result.gaming_need == NeedLevel.HIGH
        assert result.camera_need == NeedLevel.HIGH

    def test_update_profile_incremental(self):
        """测试增量更新 profile"""
        service = SessionService()
        session_id = service.create_session()

        # 第一次更新：设置预算
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_max=3000
        )
        result1 = service.update_profile(session_id, intent1)
        assert result1.budget_max == 3000
        assert result1.gaming_need is None

        # 第二次更新：添加游戏需求
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        result2 = service.update_profile(session_id, intent2)

        # 预算应该保留，游戏需求应该添加
        assert result2.budget_max == 3000
        assert result2.gaming_need == NeedLevel.HIGH

    def test_update_profile_merges_brands(self):
        """测试品牌偏好的合并"""
        service = SessionService()
        session_id = service.create_session()

        # 第一次：设置品牌偏好
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["华为", "小米"]
        )
        result1 = service.update_profile(session_id, intent1)
        assert set(result1.brand_preference) == {"华为", "小米"}

        # 第二次：添加新品牌
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["OPPO"]
        )
        result2 = service.update_profile(session_id, intent2)

        # 品牌应该合并
        assert set(result2.brand_preference) == {"华为", "小米", "OPPO"}

    def test_update_profile_no_session_creates_it(self):
        """测试更新不存在的会话时自动创建"""
        service = SessionService()
        non_existent = "new-session-id"

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_max=5000,
            features=["续航"]
        )

        result = service.update_profile(non_existent, intent)

        assert service.session_exists(non_existent)
        assert result.budget_max == 5000
        assert result.battery_need == NeedLevel.HIGH

    def test_profile_is_complete(self):
        """测试 profile 完整性判断"""
        service = SessionService()
        session_id = service.create_session()

        # 不完整的 profile
        profile1 = UserProfile(budget_max=3000)
        service.save_profile(session_id, profile1)
        result1 = service.get_profile(session_id)
        assert not result1.is_complete()

        # 完整的 profile
        profile2 = UserProfile(
            budget_max=3000,
            gaming_need=NeedLevel.HIGH
        )
        service.save_profile(session_id, profile2)
        result2 = service.get_profile(session_id)
        assert result2.is_complete()

    def test_profile_get_missing_fields(self):
        """测试获取缺失字段"""
        # 缺少所有字段
        profile1 = UserProfile()
        missing1 = profile1.get_missing_fields()
        assert "预算范围" in missing1

        # 有预算但缺少功能需求
        profile2 = UserProfile(budget_max=3000)
        missing2 = profile2.get_missing_fields()
        assert "至少一项功能需求（游戏/拍照/续航）" in missing2

        # 完整的 profile
        profile3 = UserProfile(
            budget_max=3000,
            gaming_need=NeedLevel.HIGH
        )
        missing3 = profile3.get_missing_fields()
        assert len(missing3) == 0

    def test_profile_persists_with_messages(self):
        """测试 profile 和消息可以共存"""
        service = SessionService()
        session_id = service.create_session()

        # 添加消息
        service.add_message(session_id, "user", "推荐一款手机")

        # 保存 profile
        profile = UserProfile(budget_max=3000, gaming_need=NeedLevel.HIGH)
        service.save_profile(session_id, profile)

        # 验证消息和 profile 都存在
        messages = service.get_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "推荐一款手机"

        result_profile = service.get_profile(session_id)
        assert result_profile.budget_max == 3000
        assert result_profile.gaming_need == NeedLevel.HIGH

    def test_multiple_sessions_isolated(self):
        """测试多会话的 profile 隔离"""
        service = SessionService()
        session1 = service.create_session()
        session2 = service.create_session()

        # session1 设置预算
        profile1 = UserProfile(budget_max=3000, gaming_need=NeedLevel.HIGH)
        service.save_profile(session1, profile1)

        # session2 设置不同预算
        profile2 = UserProfile(budget_max=5000, camera_need=NeedLevel.HIGH)
        service.save_profile(session2, profile2)

        # 验证隔离
        result1 = service.get_profile(session1)
        result2 = service.get_profile(session2)

        assert result1.budget_max == 3000
        assert result1.gaming_need == NeedLevel.HIGH
        assert result1.camera_need is None

        assert result2.budget_max == 5000
        assert result2.camera_need == NeedLevel.HIGH
        assert result2.gaming_need is None
