"""
多轮追问对话状态持久化测试

验证追问流程中用户回答能正确更新需求状态，实现状态合并逻辑。

测试场景：
- 第一轮：用户说"推荐手机" → profile 为空
- 第二轮：用户说"3000左右" → profile 有预算
- 第三轮：用户说"玩游戏" → profile 有预算+游戏需求
- 第四轮：用户说"拍照一般" → profile 完整
"""
import pytest
from backend.services.session import SessionService, sessions, _sessions_lock
from backend.models.schemas import (
    UserProfile,
    IntentResult,
    IntentType,
    NeedLevel
)


class TestMultiTurnClarification:
    """多轮追问对话状态持久化测试"""

    def setup_method(self):
        """每个测试前清空会话"""
        with _sessions_lock:
            sessions.clear()

    def test_four_turn_conversation_scenario(self):
        """
        四轮对话完整场景测试：
        第一轮：用户说"推荐手机" → profile 为空
        第二轮：用户说"3000左右" → profile 有预算
        第三轮：用户说"玩游戏" → profile 有预算+游戏需求
        第四轮：用户说"拍照一般" → profile 完整
        """
        service = SessionService()
        session_id = service.create_session()

        # 第一轮：用户说"推荐手机" → profile 为空
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=100000,
            brands=[],
            features=[]
        )
        profile1 = service.update_profile(session_id, intent1)

        # 验证第一轮状态
        assert profile1.budget_min is None
        assert profile1.budget_max is None
        assert profile1.gaming_need is None
        assert profile1.camera_need is None
        assert profile1.battery_need is None
        assert not profile1.is_complete()
        assert "预算范围" in " ".join(profile1.get_missing_fields())

        # 第二轮：用户说"3000左右" → profile 有预算
        # IntentService 会解析成 budget_min=2500, budget_max=3500
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2500,
            budget_max=3500,
            brands=[],
            features=[]
        )
        profile2 = service.update_profile(session_id, intent2)

        # 验证第二轮状态：有预算，但无功能需求
        assert profile2.budget_min == 2500
        assert profile2.budget_max == 3500
        assert profile2.gaming_need is None
        assert profile2.camera_need is None
        assert not profile2.is_complete()
        assert any("功能需求" in f for f in profile2.get_missing_fields())

        # 第三轮：用户说"玩游戏" → profile 有预算+游戏需求
        intent3 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=100000,
            brands=[],
            features=["游戏"]
        )
        profile3 = service.update_profile(session_id, intent3)

        # 验证第三轮状态：有预算+游戏需求，此时应该完整
        assert profile3.budget_min == 2500  # 保留第二轮的预算
        assert profile3.budget_max == 3500  # 保留第二轮的预算
        assert profile3.gaming_need == NeedLevel.HIGH
        assert profile3.camera_need is None  # 尚未设置
        assert profile3.is_complete()  # 预算+一个功能需求 = 完整

        # 第四轮：用户说"拍照一般" → profile 添加拍照需求
        # "拍照一般" 解析为 features=["拍照"]，camera_need=MEDIUM
        intent4 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,
            budget_max=100000,
            brands=[],
            features=["拍照", "一般"]
        )
        profile4 = service.update_profile(session_id, intent4)

        # 验证第四轮状态：完整且增加了拍照需求
        assert profile4.budget_min == 2500  # 保留
        assert profile4.budget_max == 3500  # 保留
        assert profile4.gaming_need == NeedLevel.HIGH  # 保留
        assert profile4.camera_need == NeedLevel.HIGH  # 新增
        assert profile4.is_complete()
        assert len(profile4.get_missing_fields()) == 0

    def test_budget_refinement_preserves_other_fields(self):
        """
        用户调整预算时保留其他已设置的字段

        场景：
        - 已有：预算 3000-5000，游戏需求 HIGH
        - 用户说："便宜点的" → 预算调整为 1500-3500
        - 验证：游戏需求仍保留
        """
        service = SessionService()
        session_id = service.create_session()

        # 初始状态：有预算和游戏需求
        initial_profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH
        )
        service.save_profile(session_id, initial_profile)

        # 用户说"便宜点的" → 预算调整
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=1500,
            budget_max=3500
        )
        updated = service.update_profile(session_id, intent)

        # 验证：预算更新，游戏需求保留
        assert updated.budget_min == 1500
        assert updated.budget_max == 3500
        assert updated.gaming_need == NeedLevel.HIGH

    def test_feature_addition_is_cumulative(self):
        """
        功能需求是累积的，不是覆盖的

        场景：
        - 第一轮：用户说"玩游戏" → gaming_need=HIGH
        - 第二轮：用户说"拍照要好" → camera_need=HIGH（不覆盖游戏需求）
        """
        service = SessionService()
        session_id = service.create_session()

        # 第一轮：设置预算和游戏需求
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000,
            features=["游戏"]
        )
        profile1 = service.update_profile(session_id, intent1)
        assert profile1.gaming_need == NeedLevel.HIGH
        assert profile1.camera_need is None

        # 第二轮：添加拍照需求
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )
        profile2 = service.update_profile(session_id, intent2)

        # 验证：游戏需求保留，拍照需求新增
        assert profile2.gaming_need == NeedLevel.HIGH
        assert profile2.camera_need == NeedLevel.HIGH
        # 预算也应保留
        assert profile2.budget_min == 2000
        assert profile2.budget_max == 4000

    def test_brand_preference_merges_and_deduplicates(self):
        """
        品牌偏好在多轮对话中合并并去重

        场景：
        - 第一轮：用户说"小米或华为" → brands=["小米", "华为"]
        - 第二轮：用户说"OPPO也可以" → brands 合并为 ["小米", "华为", "OPPO"]
        - 第三轮：用户又说"小米吧" → 品牌去重，仍是三个品牌
        """
        service = SessionService()
        session_id = service.create_session()

        # 第一轮：设置预算和品牌偏好
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=3000,
            budget_max=5000,
            brands=["小米", "华为"]
        )
        profile1 = service.update_profile(session_id, intent1)
        assert set(profile1.brand_preference) == {"小米", "华为"}

        # 第二轮：添加新品牌
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["OPPO"]
        )
        profile2 = service.update_profile(session_id, intent2)
        assert set(profile2.brand_preference) == {"小米", "华为", "OPPO"}

        # 第三轮：重复提及小米，应该去重
        intent3 = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["小米"]
        )
        profile3 = service.update_profile(session_id, intent3)
        assert set(profile3.brand_preference) == {"小米", "华为", "OPPO"}
        # 验证小米只出现一次
        assert profile3.brand_preference.count("小米") == 1

    def test_session_persistence_across_conversation(self):
        """
        验证状态在整个会话中持久保存

        模拟完整对话流程，包括消息记录和状态更新
        """
        service = SessionService()
        session_id = service.create_session()

        # 第一轮对话
        service.add_message(session_id, "user", "推荐手机")
        service.add_message(session_id, "assistant", "请问您的预算大概是多少？")
        intent1 = IntentResult(intent=IntentType.RECOMMEND)
        profile1 = service.update_profile(session_id, intent1)
        assert not profile1.is_complete()

        # 第二轮对话：用户提供预算
        service.add_message(session_id, "user", "3000左右")
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2500,
            budget_max=3500
        )
        profile2 = service.update_profile(session_id, intent2)
        assert profile2.budget_max == 3500
        assert not profile2.is_complete()

        # 第三轮对话：用户提供功能需求
        service.add_message(session_id, "assistant", "您对游戏、拍照或续航有特别要求吗？")
        service.add_message(session_id, "user", "主要玩游戏")
        intent3 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        profile3 = service.update_profile(session_id, intent3)
        assert profile3.is_complete()

        # 验证消息历史和状态都正确保存
        messages = service.get_messages(session_id)
        assert len(messages) == 5  # user-推荐手机、assistant-预算、user-3000左右、assistant-功能需求、user-玩游戏

        final_profile = service.get_profile(session_id)
        assert final_profile.budget_min == 2500
        assert final_profile.budget_max == 3500
        assert final_profile.gaming_need == NeedLevel.HIGH
        assert final_profile.is_complete()

    def test_concurrent_sessions_state_isolation(self):
        """
        多个并发会话的状态隔离

        验证不同会话的状态不会互相干扰
        """
        service = SessionService()
        session1 = service.create_session()
        session2 = service.create_session()

        # session1 的对话流程
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000,
            features=["游戏"]
        )
        profile1 = service.update_profile(session1, intent1)

        # session2 的对话流程（不同的需求）
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=5000,
            budget_max=8000,
            features=["拍照"]
        )
        profile2 = service.update_profile(session2, intent2)

        # 验证两个会话的状态完全隔离
        p1 = service.get_profile(session1)
        p2 = service.get_profile(session2)

        assert p1.budget_min == 2000
        assert p1.budget_max == 4000
        assert p1.gaming_need == NeedLevel.HIGH
        assert p1.camera_need is None

        assert p2.budget_min == 5000
        assert p2.budget_max == 8000
        assert p2.camera_need == NeedLevel.HIGH
        assert p2.gaming_need is None

    def test_update_from_intent_with_null_values_preserves_existing(self):
        """
        IntentResult 中的默认值（空值）不应覆盖已有状态

        这是关键的增量更新测试
        """
        service = SessionService()
        session_id = service.create_session()

        # 设置初始状态
        initial = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM
        )
        service.save_profile(session_id, initial)

        # 用户新消息只包含品牌，其他字段为空
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["小米"]
        )
        updated = service.update_profile(session_id, intent)

        # 验证：预算和功能需求都保留，只添加品牌
        assert updated.budget_min == 2000
        assert updated.budget_max == 4000
        assert updated.gaming_need == NeedLevel.HIGH
        assert updated.camera_need == NeedLevel.MEDIUM
        assert updated.brand_preference == ["小米"]

    def test_feature_level_not_overwritten_by_newer_input(self):
        """
        功能需求级别不会被后来的输入降低

        如果用户先说"游戏很重要"（HIGH），后说"偶尔玩玩"，
        IntentResult 可能解析为 features=["游戏"]，
        此时应该保留 HIGH 级别，不应该覆盖为更低的级别。

        当前实现：features 只推断 HIGH/MEDIUM，不会降低已设置的级别。
        """
        service = SessionService()
        session_id = service.create_session()

        # 初始：游戏需求 HIGH
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=3000,
            features=["游戏"]
        )
        profile1 = service.update_profile(session_id, intent1)
        assert profile1.gaming_need == NeedLevel.HIGH

        # 后续：用户说"偶尔玩玩游戏"
        # IntentResult.features=["游戏"]，但不应降低已有的 HIGH
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        profile2 = service.update_profile(session_id, intent2)

        # 验证：游戏需求仍为 HIGH（不被重复设置覆盖）
        assert profile2.gaming_need == NeedLevel.HIGH


class TestUserProfileUpdateFromIntentEnhancements:
    """
    测试 update_from_intent 方法的增量更新逻辑
    """

    def test_empty_intent_result_no_change(self):
        """空的 IntentResult 不应改变现有状态"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        empty_intent = IntentResult(intent=IntentType.RECOMMEND)
        updated = profile.update_from_intent(empty_intent)

        assert updated.budget_min == 2000
        assert updated.budget_max == 4000
        assert updated.gaming_need == NeedLevel.HIGH

    def test_default_budget_values_do_not_override(self):
        """
        IntentResult 的默认预算值不应覆盖已设置的预算

        默认值：budget_min=0, budget_max=100000
        这些不应覆盖用户已设置的预算
        """
        profile = UserProfile(budget_min=3000, budget_max=5000)

        # IntentResult 使用默认预算值
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,  # 默认值
            budget_max=100000  # 默认值
        )
        updated = profile.update_from_intent(intent)

        # 验证：预算保留，不被默认值覆盖
        assert updated.budget_min == 3000
        assert updated.budget_max == 5000

    def test_brand_preference_none_to_list(self):
        """品牌偏好从 None 到有值的转换"""
        profile = UserProfile(budget_min=2000)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["华为"]
        )
        updated = profile.update_from_intent(intent)

        assert updated.brand_preference == ["华为"]

    def test_brand_preference_list_to_more(self):
        """品牌偏好从有值到更多值（合并）"""
        profile = UserProfile(
            budget_min=2000,
            brand_preference=["华为"]
        )
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["小米", "OPPO"]
        )
        updated = profile.update_from_intent(intent)

        assert set(updated.brand_preference) == {"华为", "小米", "OPPO"}

    def test_all_feature_types_inferred(self):
        """测试所有功能需求类型的推断"""
        profile = UserProfile()

        # 游戏相关
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏", "电竞", "性能"]
        )
        updated1 = profile.update_from_intent(intent1)
        assert updated1.gaming_need == NeedLevel.HIGH

        # 拍照相关
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照", "影像", "相机"]
        )
        updated2 = profile.update_from_intent(intent2)
        assert updated2.camera_need == NeedLevel.HIGH

        # 续航相关
        intent3 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航", "电池"]
        )
        updated3 = profile.update_from_intent(intent3)
        assert updated3.battery_need == NeedLevel.HIGH

        # 快充（推断为续航 MEDIUM）
        intent4 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["快充"]
        )
        updated4 = profile.update_from_intent(intent4)
        assert updated4.battery_need == NeedLevel.MEDIUM

    def test_profile_immutability_on_update(self):
        """验证 update_from_intent 返回新实例，原实例不变"""
        original = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.LOW
        )
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_max=5000,
            features=["拍照"]
        )
        updated = original.update_from_intent(intent)

        # 原实例不变
        assert original.budget_min == 2000
        assert original.budget_max is None
        assert original.gaming_need == NeedLevel.LOW
        assert original.camera_need is None

        # 新实例有更新
        assert updated.budget_min == 2000  # 保留
        assert updated.budget_max == 5000  # 新增
        assert updated.gaming_need == NeedLevel.LOW  # 保留
        assert updated.camera_need == NeedLevel.HIGH  # 新增


class TestSessionServiceProfileMethods:
    """测试 SessionService 的 profile 相关方法"""

    def setup_method(self):
        """每个测试前清空会话"""
        with _sessions_lock:
            sessions.clear()

    def test_update_profile_creates_session_if_needed(self):
        """update_profile 自动创建不存在会话"""
        service = SessionService()
        new_session_id = "auto-created-session"

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_max=5000
        )
        profile = service.update_profile(new_session_id, intent)

        # 验证会话被创建
        assert service.session_exists(new_session_id)
        assert profile.budget_max == 5000

    def test_get_profile_returns_none_for_nonexistent(self):
        """get_profile 对不存在的会话返回 None"""
        service = SessionService()
        result = service.get_profile("nonexistent-session")
        assert result is None

    def test_save_profile_overwrites_existing(self):
        """save_profile 完全覆盖现有 profile"""
        service = SessionService()
        session_id = service.create_session()

        # 第一次保存
        profile1 = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH
        )
        service.save_profile(session_id, profile1)

        # 第二次保存（完全不同的 profile）
        profile2 = UserProfile(
            budget_max=5000,
            camera_need=NeedLevel.MEDIUM
        )
        service.save_profile(session_id, profile2)

        # 验证：完全覆盖
        result = service.get_profile(session_id)
        assert result.budget_min is None
        assert result.budget_max == 5000
        assert result.gaming_need is None
        assert result.camera_need == NeedLevel.MEDIUM

    def test_update_profile_is_incremental(self):
        """update_profile 是增量更新，不是覆盖"""
        service = SessionService()
        session_id = service.create_session()

        # 第一次更新
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000
        )
        profile1 = service.update_profile(session_id, intent1)

        # 第二次更新（增量）
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        profile2 = service.update_profile(session_id, intent2)

        # 验证：预算保留，功能需求新增
        assert profile2.budget_min == 2000
        assert profile2.budget_max == 4000
        assert profile2.gaming_need == NeedLevel.HIGH