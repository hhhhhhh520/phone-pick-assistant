"""
意图识别服务 fallback 方法测试

测试 _fallback_intent_recognition 的规则解析能力：
- 预算提取
- 品牌提取
- 功能需求提取
- 意图类型识别
"""
import pytest
from backend.services.intent import IntentService
from backend.models.schemas import IntentType


class TestFallbackBudgetExtraction:
    """测试预算提取规则"""

    def setup_method(self):
        self.service = IntentService()

    def test_extract_thousand_yuan_price(self):
        """测试 '三千价位' 格式"""
        result = self.service._fallback_intent_recognition("推荐一款三千价位的手机")
        assert result.budget_min == 2500
        assert result.budget_max == 3500

    def test_extract_specific_price_around(self):
        """测试 '3000左右' 格式"""
        result = self.service._fallback_intent_recognition("3000左右的手机")
        assert result.budget_min == 2500
        assert result.budget_max == 3500

    def test_extract_price_range(self):
        """测试 '2000-4000元' 格式"""
        result = self.service._fallback_intent_recognition("推荐2000-4000元的手机")
        assert result.budget_min == 2000
        assert result.budget_max == 4000

    def test_extract_price_range_to(self):
        """测试 '2000到4000元' 格式"""
        result = self.service._fallback_intent_recognition("2000到4000元的手机")
        assert result.budget_min == 2000
        assert result.budget_max == 4000

    def test_extract_under_price(self):
        """测试 '不超过3000元' 格式"""
        result = self.service._fallback_intent_recognition("不超过3000元的手机")
        assert result.budget_min == 0
        assert result.budget_max == 3000

    def test_extract_wan_yuan(self):
        """测试 '一万以内' 格式"""
        result = self.service._fallback_intent_recognition("一万以内的手机")
        assert result.budget_min == 0
        assert result.budget_max == 10000

    def test_no_budget_returns_default(self):
        """无预算信息返回默认值"""
        result = self.service._fallback_intent_recognition("推荐一款手机")
        assert result.budget_min == 0
        assert result.budget_max == 100000


class TestFallbackBrandExtraction:
    """测试品牌提取规则"""

    def setup_method(self):
        self.service = IntentService()

    def test_extract_xiaomi(self):
        """测试提取小米品牌"""
        result = self.service._fallback_intent_recognition("推荐小米手机")
        assert "小米" in result.brands

    def test_extract_huawei(self):
        """测试提取华为品牌"""
        result = self.service._fallback_intent_recognition("华为和荣耀都可以")
        assert "华为" in result.brands
        assert "荣耀" in result.brands

    def test_extract_apple(self):
        """测试提取苹果品牌"""
        result = self.service._fallback_intent_recognition("想要iPhone")
        assert "苹果" in result.brands

    def test_extract_multiple_brands(self):
        """测试提取多个品牌"""
        result = self.service._fallback_intent_recognition("小米、华为或者OPPO")
        assert "小米" in result.brands
        assert "华为" in result.brands
        assert "OPPO" in result.brands

    def test_no_brand_returns_empty(self):
        """无品牌信息返回空列表"""
        result = self.service._fallback_intent_recognition("推荐一款3000元的手机")
        assert result.brands == []


class TestFallbackFeatureExtraction:
    """测试功能需求提取规则"""

    def setup_method(self):
        self.service = IntentService()

    def test_extract_gaming_feature(self):
        """测试提取游戏需求"""
        result = self.service._fallback_intent_recognition("用来打游戏")
        assert "游戏" in result.features

    def test_extract_camera_feature(self):
        """测试提取拍照需求"""
        result = self.service._fallback_intent_recognition("拍照要好")
        assert "拍照" in result.features

    def test_extract_battery_feature(self):
        """测试提取续航需求"""
        result = self.service._fallback_intent_recognition("续航要长")
        assert "续航" in result.features

    def test_extract_fast_charge_feature(self):
        """测试提取快充需求"""
        result = self.service._fallback_intent_recognition("充电要快")
        assert "快充" in result.features

    def test_extract_multiple_features(self):
        """测试提取多个功能需求"""
        result = self.service._fallback_intent_recognition("要玩游戏，拍照也要好，续航长一点")
        assert "游戏" in result.features
        assert "拍照" in result.features
        assert "续航" in result.features

    def test_no_feature_returns_empty(self):
        """无功能需求返回空列表"""
        result = self.service._fallback_intent_recognition("推荐一款小米手机")
        assert result.features == []


class TestFallbackIntentType:
    """测试意图类型识别"""

    def setup_method(self):
        self.service = IntentService()

    def test_recommend_intent(self):
        """测试推荐意图"""
        result = self.service._fallback_intent_recognition("推荐一款手机")
        assert result.intent == IntentType.RECOMMEND

    def test_compare_intent(self):
        """测试对比意图"""
        result = self.service._fallback_intent_recognition("对比小米和华为")
        assert result.intent == IntentType.COMPARE

    def test_filter_intent(self):
        """测试筛选意图"""
        result = self.service._fallback_intent_recognition("只看小米的手机")
        assert result.intent == IntentType.FILTER

    def test_compare_intent_which_better(self):
        """测试 '哪个好' 触发对比意图"""
        result = self.service._fallback_intent_recognition("小米和华为哪个好")
        assert result.intent == IntentType.COMPARE


class TestFallbackCombinedExtraction:
    """测试综合提取能力"""

    def setup_method(self):
        self.service = IntentService()

    def test_budget_and_feature(self):
        """测试预算+功能需求"""
        result = self.service._fallback_intent_recognition("3000左右玩游戏")
        assert result.budget_min == 2500
        assert result.budget_max == 3500
        assert "游戏" in result.features

    def test_budget_and_brand(self):
        """测试预算+品牌"""
        result = self.service._fallback_intent_recognition("3000元以内的小米手机")
        assert result.budget_max == 3000
        assert "小米" in result.brands

    def test_all_fields(self):
        """测试所有字段"""
        result = self.service._fallback_intent_recognition("3000到4000的小米，主要玩游戏和拍照")
        assert result.budget_min == 3000
        assert result.budget_max == 4000
        assert "小米" in result.brands
        assert "游戏" in result.features
        assert "拍照" in result.features

    def test_gaming_keywords_variants(self):
        """测试游戏相关的多种表达"""
        gaming_variants = [
            "打游戏",
            "玩游戏",
            "电竞手机",
            "打王者",
            "玩原神"
        ]
        for variant in gaming_variants:
            result = self.service._fallback_intent_recognition(f"推荐{variant}的手机")
            assert "游戏" in result.features, f"Failed for: {variant}"

    def test_camera_keywords_variants(self):
        """测试拍照相关的多种表达"""
        camera_variants = [
            "拍照",
            "照相",
            "摄影",
            "自拍",
            "夜景拍摄"
        ]
        for variant in camera_variants:
            result = self.service._fallback_intent_recognition(f"推荐{variant}好的手机")
            assert "拍照" in result.features, f"Failed for: {variant}"


class TestFallbackEdgeCases:
    """测试边界情况"""

    def setup_method(self):
        self.service = IntentService()

    def test_empty_message(self):
        """空消息"""
        result = self.service._fallback_intent_recognition("")
        assert result.intent == IntentType.RECOMMEND
        assert result.budget_min == 0
        assert result.budget_max == 100000
        assert result.brands == []
        assert result.features == []

    def test_unknown_content(self):
        """无法识别的内容"""
        result = self.service._fallback_intent_recognition("随便说说")
        assert result.intent == IntentType.RECOMMEND

    def test_large_budget(self):
        """大额预算"""
        result = self.service._fallback_intent_recognition("2万以内")
        assert result.budget_max == 20000

    def test_small_budget(self):
        """小额预算"""
        result = self.service._fallback_intent_recognition("1000元左右")
        assert result.budget_min == 500
        assert result.budget_max == 1500
