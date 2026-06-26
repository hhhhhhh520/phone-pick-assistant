"""
UserProfile 模型单元测试

测试覆盖：
- 模型创建和默认值
- is_complete() 完整性判断
- get_missing_fields() 缺失字段检测
- update_from_intent() 从意图结果更新状态
"""
import pytest
from backend.models.schemas import (
    UserProfile,
    NeedLevel,
    IntentResult,
    IntentType
)


class TestUserProfileCreation:
    """测试 UserProfile 创建和默认值"""

    def test_create_empty_profile(self):
        """创建空的用户画像"""
        profile = UserProfile()
        assert profile.budget_min is None
        assert profile.budget_max is None
        assert profile.gaming_need is None
        assert profile.camera_need is None
        assert profile.battery_need is None
        assert profile.brand_preference is None

    def test_create_with_budget_only(self):
        """只设置预算"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        assert profile.budget_min == 2000
        assert profile.budget_max == 4000
        assert profile.gaming_need is None

    def test_create_with_needs_only(self):
        """只设置功能需求"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM
        )
        assert profile.gaming_need == NeedLevel.HIGH
        assert profile.camera_need == NeedLevel.MEDIUM
        assert profile.battery_need is None

    def test_create_full_profile(self):
        """创建完整用户画像"""
        profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.LOW,
            battery_need=NeedLevel.MEDIUM,
            brand_preference=["小米", "华为"]
        )
        assert profile.budget_min == 3000
        assert profile.budget_max == 5000
        assert profile.gaming_need == NeedLevel.HIGH
        assert profile.camera_need == NeedLevel.LOW
        assert profile.battery_need == NeedLevel.MEDIUM
        assert profile.brand_preference == ["小米", "华为"]


class TestIsComplete:
    """测试 is_complete() 完整性判断"""

    def test_empty_profile_not_complete(self):
        """空画像不完整"""
        profile = UserProfile()
        assert profile.is_complete() is False

    def test_budget_only_not_complete(self):
        """只有预算不完整"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        assert profile.is_complete() is False

    def test_feature_only_not_complete(self):
        """只有功能需求不完整"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        assert profile.is_complete() is False

    def test_budget_and_one_feature_complete(self):
        """预算 + 一个功能需求 = 完整"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        assert profile.is_complete() is True

    def test_budget_max_only_and_feature_complete(self):
        """只有预算上限 + 功能需求 = 完整"""
        profile = UserProfile(
            budget_max=5000,
            camera_need=NeedLevel.HIGH
        )
        assert profile.is_complete() is True

    def test_budget_min_only_and_feature_complete(self):
        """只有预算下限 + 功能需求 = 完整"""
        profile = UserProfile(
            budget_min=3000,
            battery_need=NeedLevel.MEDIUM
        )
        assert profile.is_complete() is True

    def test_all_fields_complete(self):
        """所有字段都有值"""
        profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            battery_need=NeedLevel.LOW,
            brand_preference=["小米"]
        )
        assert profile.is_complete() is True

    def test_no_brand_still_complete(self):
        """没有品牌偏好仍然完整（品牌是可选的）"""
        profile = UserProfile(
            budget_min=2000,
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        assert profile.brand_preference is None
        assert profile.is_complete() is True


class TestGetMissingFields:
    """测试 get_missing_fields() 缺失字段检测"""

    def test_empty_profile_missing_all(self):
        """空画像缺少预算和功能需求"""
        profile = UserProfile()
        missing = profile.get_missing_fields()
        assert "预算范围" in missing
        assert any("功能需求" in m for m in missing)

    def test_budget_only_missing_features(self):
        """只有预算，缺少功能需求"""
        profile = UserProfile(budget_min=2000, budget_max=4000)
        missing = profile.get_missing_fields()
        assert "预算范围" not in missing
        assert any("功能需求" in m for m in missing)

    def test_feature_only_missing_budget(self):
        """只有功能需求，缺少预算"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        missing = profile.get_missing_fields()
        assert "预算范围" in missing
        assert not any("功能需求" in m for m in missing)

    def test_complete_profile_no_missing(self):
        """完整画像没有缺失"""
        profile = UserProfile(
            budget_min=3000,
            gaming_need=NeedLevel.HIGH
        )
        missing = profile.get_missing_fields()
        assert len(missing) == 0

    def test_partial_features_not_missing(self):
        """有部分功能需求时不报告缺失（因为至少有一个就够了）"""
        profile = UserProfile(
            budget_min=3000,
            gaming_need=NeedLevel.HIGH
        )
        # 只设置了游戏需求，拍照和续航为空，但不需要报告
        missing = profile.get_missing_fields()
        assert "拍照需求" not in missing
        assert "续航需求" not in missing


class TestUpdateFromIntent:
    """测试 update_from_intent() 从意图结果更新状态"""

    def test_update_budget_from_intent(self):
        """从意图结果更新预算"""
        profile = UserProfile()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000
        )
        updated = profile.update_from_intent(intent)
        assert updated.budget_min == 2000
        assert updated.budget_max == 4000

    def test_update_brands_from_intent(self):
        """从意图结果更新品牌偏好"""
        profile = UserProfile()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["小米", "华为"]
        )
        updated = profile.update_from_intent(intent)
        assert "小米" in updated.brand_preference
        assert "华为" in updated.brand_preference

    def test_merge_brands_on_update(self):
        """更新品牌时合并现有偏好"""
        profile = UserProfile(brand_preference=["小米"])
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["华为", "OPPO"]
        )
        updated = profile.update_from_intent(intent)
        assert "小米" in updated.brand_preference
        assert "华为" in updated.brand_preference
        assert "OPPO" in updated.brand_preference

    def test_deduplicate_brands(self):
        """品牌去重"""
        profile = UserProfile(brand_preference=["小米"])
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["小米", "华为"]
        )
        updated = profile.update_from_intent(intent)
        assert updated.brand_preference.count("小米") == 1

    def test_infer_gaming_need_from_features(self):
        """从 features 推断游戏需求"""
        profile = UserProfile()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        updated = profile.update_from_intent(intent)
        assert updated.gaming_need == NeedLevel.HIGH

    def test_infer_camera_need_from_features(self):
        """从 features 推断拍照需求"""
        profile = UserProfile()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照", "影像"]
        )
        updated = profile.update_from_intent(intent)
        assert updated.camera_need == NeedLevel.HIGH

    def test_infer_battery_need_from_features(self):
        """从 features 推断续航需求"""
        profile = UserProfile()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航", "电池"]
        )
        updated = profile.update_from_intent(intent)
        assert updated.battery_need == NeedLevel.HIGH

    def test_infer_battery_need_from_fast_charge(self):
        """从快充需求推断续航需求（中等）"""
        profile = UserProfile()
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["快充"]
        )
        updated = profile.update_from_intent(intent)
        assert updated.battery_need == NeedLevel.MEDIUM

    def test_preserve_existing_fields(self):
        """更新时保留未修改的字段"""
        profile = UserProfile(
            budget_min=2000,
            gaming_need=NeedLevel.HIGH
        )
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_max=5000,
            features=["拍照"]
        )
        updated = profile.update_from_intent(intent)
        # 保留原有的 budget_min 和 gaming_need
        assert updated.budget_min == 2000
        assert updated.gaming_need == NeedLevel.HIGH
        # 新增的值
        assert updated.budget_max == 5000
        assert updated.camera_need == NeedLevel.HIGH

    def test_do_not_override_with_default_values(self):
        """不使用默认值覆盖现有字段"""
        profile = UserProfile(budget_min=3000)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0,  # 默认值，不应覆盖
            budget_max=100000  # 默认值，不应覆盖
        )
        updated = profile.update_from_intent(intent)
        assert updated.budget_min == 3000  # 保留原值
        assert updated.budget_max is None  # 未设置

    def test_update_returns_new_instance(self):
        """更新返回新实例，不修改原实例"""
        profile = UserProfile(gaming_need=NeedLevel.LOW)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )
        updated = profile.update_from_intent(intent)
        # 原实例不变
        assert profile.gaming_need == NeedLevel.LOW
        assert profile.camera_need is None
        # 新实例有更新
        assert updated.gaming_need == NeedLevel.LOW
        assert updated.camera_need == NeedLevel.HIGH


class TestNeedLevel:
    """测试 NeedLevel 枚举"""

    def test_need_level_values(self):
        """测试枚举值"""
        assert NeedLevel.HIGH.value == "高"
        assert NeedLevel.MEDIUM.value == "中"
        assert NeedLevel.LOW.value == "低"

    def test_need_level_from_string(self):
        """从字符串创建枚举"""
        assert NeedLevel("高") == NeedLevel.HIGH
        assert NeedLevel("中") == NeedLevel.MEDIUM
        assert NeedLevel("低") == NeedLevel.LOW


class TestIntegration:
    """集成测试：模拟多轮对话场景"""

    def test_multi_turn_conversation(self):
        """模拟多轮对话：用户逐步补充需求"""
        # 第一轮：用户只说了预算
        profile = UserProfile()
        intent1 = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000
        )
        profile = profile.update_from_intent(intent1)
        assert profile.is_complete() is False
        assert "功能需求" in " ".join(profile.get_missing_fields())

        # 第二轮：用户说想玩游戏
        intent2 = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )
        profile = profile.update_from_intent(intent2)
        assert profile.is_complete() is True
        assert len(profile.get_missing_fields()) == 0

        # 第三轮：用户补充品牌偏好
        intent3 = IntentResult(
            intent=IntentType.RECOMMEND,
            brands=["小米", "华为"]
        )
        profile = profile.update_from_intent(intent3)
        assert profile.is_complete() is True
        assert set(profile.brand_preference) == {"小米", "华为"}

    def test_refine_budget_in_conversation(self):
        """对话中调整预算"""
        profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH
        )

        # 用户说"便宜点的"
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=1500,
            budget_max=3500
        )
        profile = profile.update_from_intent(intent)
        assert profile.budget_min == 1500
        assert profile.budget_max == 3500
        assert profile.gaming_need == NeedLevel.HIGH  # 保留
