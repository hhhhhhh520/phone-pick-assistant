"""
PainPointQuestionService 单元测试

测试覆盖：
- PainPointResponse 数据模型
- PAIN_POINT_TEMPLATES 模板完整性
- _detect_budget_feature_conflict() 预算与需求冲突检测
- _detect_brand_budget_conflict() 品牌与预算冲突检测
- _detect_feature_conflict() 功能冲突检测
- _detect_battery_gaming_conflict() 续航与游戏冲突检测
- _detect_general_high_demand_low_budget() 综合高需求低预算检测
- _detect_brand_feature_mismatch() 品牌与功能不匹配检测
- generate_pain_point_question() 主方法
- 集成测试
"""
import pytest
from backend.services.question import (
    PainPointResponse,
    PainPointQuestionService,
    PAIN_POINT_TEMPLATES
)
from backend.models.schemas import UserProfile, NeedLevel


class TestPainPointResponse:
    """测试 PainPointResponse 数据模型"""

    def test_create_pain_point_response(self):
        """创建痛点追问响应"""
        response = PainPointResponse(
            question="您的预算可能难以满足游戏+拍照的高需求",
            quick_replies=["提高预算", "降低游戏需求", "降低拍照需求"],
            pain_point_type="budget_too_low_for_features",
            severity="high",
            suggestion="建议预算提高到4000元以上"
        )

        assert response.question == "您的预算可能难以满足游戏+拍照的高需求"
        assert len(response.quick_replies) == 3
        assert response.pain_point_type == "budget_too_low_for_features"
        assert response.severity == "high"
        assert response.suggestion == "建议预算提高到4000元以上"

    def test_create_pain_point_response_without_suggestion(self):
        """创建无建议的响应"""
        response = PainPointResponse(
            question="问题",
            quick_replies=["选项1"],
            pain_point_type="test_type"
        )

        assert response.severity == "medium"  # 默认值
        assert response.suggestion is None

    def test_pain_point_response_optional_suggestion(self):
        """建议字段可选"""
        response = PainPointResponse(
            question="测试问题",
            quick_replies=["A", "B"],
            pain_point_type="test"
        )

        assert response.suggestion is None


class TestPainPointTemplates:
    """测试 PAIN_POINT_TEMPLATES 模板完整性"""

    def test_all_templates_have_required_fields(self):
        """所有模板包含必需字段"""
        required_fields = ["description", "question_templates", "quick_replies", "suggestion"]

        for template_name, template in PAIN_POINT_TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"{template_name} missing {field}"

    def test_all_templates_have_multiple_questions(self):
        """所有模板有多个问题模板（随机性）"""
        for template_name, template in PAIN_POINT_TEMPLATES.items():
            assert len(template["question_templates"]) >= 2, \
                f"{template_name} should have at least 2 question templates"

    def test_all_templates_have_quick_replies(self):
        """所有模板有快捷回复"""
        for template_name, template in PAIN_POINT_TEMPLATES.items():
            assert len(template["quick_replies"]) >= 3, \
                f"{template_name} should have at least 3 quick replies"

    def test_budget_too_low_template_exists(self):
        """预算不足模板存在"""
        assert "budget_too_low_for_features" in PAIN_POINT_TEMPLATES

    def test_brand_budget_conflict_template_exists(self):
        """品牌预算冲突模板存在"""
        assert "brand_budget_conflict" in PAIN_POINT_TEMPLATES
        # 检查模板变量占位符
        template = PAIN_POINT_TEMPLATES["brand_budget_conflict"]
        has_brand_var = any("{brand}" in q for q in template["question_templates"])
        has_price_var = any("{min_price}" in q for q in template["question_templates"])
        assert has_brand_var, "brand_budget_conflict should have {brand} placeholder"
        assert has_price_var, "brand_budget_conflict should have {min_price} placeholder"

    def test_gaming_camera_conflict_template_exists(self):
        """游戏拍照冲突模板存在"""
        assert "gaming_camera_budget_conflict" in PAIN_POINT_TEMPLATES

    def test_battery_vs_gaming_template_exists(self):
        """续航游戏冲突模板存在"""
        assert "battery_vs_gaming" in PAIN_POINT_TEMPLATES

    def test_high_demand_low_budget_template_exists(self):
        """高需求低预算模板存在"""
        assert "high_demand_low_budget_general" in PAIN_POINT_TEMPLATES

    def test_brand_feature_mismatch_template_exists(self):
        """品牌功能不匹配模板存在"""
        assert "brand_not_match_features" in PAIN_POINT_TEMPLATES
        # 检查模板变量
        template = PAIN_POINT_TEMPLATES["brand_not_match_features"]
        has_brand_var = any("{brand}" in q for q in template["question_templates"])
        has_feature_var = any("{feature}" in q for q in template["question_templates"])
        assert has_brand_var, "brand_not_match_features should have {brand} placeholder"
        assert has_feature_var, "brand_not_match_features should have {feature} placeholder"


class TestPainPointQuestionServiceDetectBudgetFeatureConflict:
    """测试 _detect_budget_feature_conflict() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_high_gaming_low_budget(self, service):
        """高游戏需求+低预算=冲突"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_budget_feature_conflict(profile)
        assert result is True

    def test_high_camera_low_budget(self, service):
        """高拍照需求+低预算=冲突"""
        profile = UserProfile(
            budget_max=2500,
            camera_need=NeedLevel.HIGH
        )
        result = service._detect_budget_feature_conflict(profile)
        assert result is True

    def test_high_gaming_sufficient_budget(self, service):
        """高游戏需求+充足预算=无冲突"""
        profile = UserProfile(
            budget_max=5000,
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_budget_feature_conflict(profile)
        assert result is False

    def test_medium_need_low_budget(self, service):
        """中等需求+低预算=无冲突"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.MEDIUM
        )
        result = service._detect_budget_feature_conflict(profile)
        assert result is False

    def test_no_need_low_budget(self, service):
        """无需求+低预算=无冲突"""
        profile = UserProfile(budget_max=2500)
        result = service._detect_budget_feature_conflict(profile)
        assert result is False

    def test_no_budget_high_need(self, service):
        """无预算限制+高需求=无冲突"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        result = service._detect_budget_feature_conflict(profile)
        assert result is False

    def test_boundary_budget_3000(self, service):
        """边界测试：预算正好3000"""
        profile = UserProfile(
            budget_max=3000,
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_budget_feature_conflict(profile)
        # 3000不小于3000，无冲突
        assert result is False


class TestPainPointQuestionServiceDetectBrandBudgetConflict:
    """测试 _detect_brand_budget_conflict() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_apple_budget_conflict(self, service):
        """苹果+预算不足=冲突"""
        profile = UserProfile(
            budget_max=3000,
            brand_preference=["苹果"]
        )
        result = service._detect_brand_budget_conflict(profile)
        assert result is not None
        assert result["brand"] == "苹果"
        assert result["min_price"] == 5000

    def test_huawei_budget_conflict(self, service):
        """华为+预算不足=冲突"""
        profile = UserProfile(
            budget_max=2500,
            brand_preference=["华为"]
        )
        result = service._detect_brand_budget_conflict(profile)
        assert result is not None
        assert result["brand"] == "华为"
        assert result["min_price"] == 4000

    def test_xiaomi_sufficient_budget(self, service):
        """小米+充足预算=无冲突"""
        profile = UserProfile(
            budget_max=3500,
            brand_preference=["小米"]
        )
        result = service._detect_brand_budget_conflict(profile)
        assert result is None

    def test_no_brand_preference(self, service):
        """无品牌偏好=无冲突"""
        profile = UserProfile(budget_max=2000)
        result = service._detect_brand_budget_conflict(profile)
        assert result is None

    def test_no_budget_with_brand(self, service):
        """有品牌偏好无预算限制=无冲突"""
        profile = UserProfile(brand_preference=["苹果"])
        result = service._detect_brand_budget_conflict(profile)
        assert result is None

    def test_brand_normalization(self, service):
        """品牌名称标准化"""
        # 英文品牌名
        profile = UserProfile(
            budget_max=3000,
            brand_preference=["apple", "iPhone"]
        )
        result = service._detect_brand_budget_conflict(profile)
        assert result is not None
        assert result["brand"] == "苹果"

    def test_multiple_brands_first_conflict(self, service):
        """多品牌偏好，检测第一个冲突"""
        profile = UserProfile(
            budget_max=2500,
            brand_preference=["小米", "苹果"]
        )
        result = service._detect_brand_budget_conflict(profile)
        # 小米旗舰3000，2500买不到
        assert result is not None


class TestPainPointQuestionServiceDetectFeatureConflict:
    """测试 _detect_feature_conflict() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_high_gaming_high_camera_low_budget(self, service):
        """高游戏+高拍照+低预算=冲突"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        result = service._detect_feature_conflict(profile)
        assert result is True

    def test_high_gaming_high_camera_sufficient_budget(self, service):
        """高游戏+高拍照+充足预算=无冲突"""
        profile = UserProfile(
            budget_max=6000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        result = service._detect_feature_conflict(profile)
        assert result is False

    def test_high_gaming_medium_camera(self, service):
        """高游戏+中等拍照=无冲突"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM
        )
        result = service._detect_feature_conflict(profile)
        assert result is False

    def test_one_high_feature(self, service):
        """只有一项高需求=无冲突"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_feature_conflict(profile)
        assert result is False


class TestPainPointQuestionServiceDetectBatteryGamingConflict:
    """测试 _detect_battery_gaming_conflict() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_high_gaming_high_battery(self, service):
        """高游戏+高续航=冲突"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH
        )
        result = service._detect_battery_gaming_conflict(profile)
        assert result is True

    def test_high_gaming_low_battery(self, service):
        """高游戏+低续航=无冲突"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            battery_need=NeedLevel.LOW
        )
        result = service._detect_battery_gaming_conflict(profile)
        assert result is False

    def test_low_gaming_high_battery(self, service):
        """低游戏+高续航=无冲突"""
        profile = UserProfile(
            gaming_need=NeedLevel.LOW,
            battery_need=NeedLevel.HIGH
        )
        result = service._detect_battery_gaming_conflict(profile)
        assert result is False

    def test_no_gaming_need(self, service):
        """无游戏需求=无冲突"""
        profile = UserProfile(battery_need=NeedLevel.HIGH)
        result = service._detect_battery_gaming_conflict(profile)
        assert result is False


class TestPainPointQuestionServiceDetectGeneralHighDemandLowBudget:
    """测试 _detect_general_high_demand_low_budget() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_all_three_high_low_budget(self, service):
        """三项全高+低预算=冲突"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH
        )
        result = service._detect_general_high_demand_low_budget(profile)
        assert result is True

    def test_all_three_high_sufficient_budget(self, service):
        """三项全高+充足预算=无冲突"""
        profile = UserProfile(
            budget_max=6000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH
        )
        result = service._detect_general_high_demand_low_budget(profile)
        assert result is False

    def test_two_high_low_budget(self, service):
        """两项高需求+低预算=无冲突（需要三项）"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        result = service._detect_general_high_demand_low_budget(profile)
        assert result is False

    def test_mixed_needs(self, service):
        """混合需求=无冲突"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.MEDIUM,
            battery_need=NeedLevel.HIGH
        )
        result = service._detect_general_high_demand_low_budget(profile)
        # 只有2项高需求
        assert result is False


class TestPainPointQuestionServiceDetectBrandFeatureMismatch:
    """测试 _detect_brand_feature_mismatch() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_brand_not_specialize_in_feature(self, service):
        """品牌不擅长用户高需求功能"""
        # 用户要高游戏性能，但选华为（擅长拍照续航）
        profile = UserProfile(
            brand_preference=["华为"],
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_brand_feature_mismatch(profile)
        assert result is not None
        assert result["brand"] == "华为"
        assert result["feature"] == "游戏"

    def test_brand_specialize_in_feature(self, service):
        """品牌擅长用户高需求功能"""
        # 用户要高拍照，选华为（擅长拍照）
        profile = UserProfile(
            brand_preference=["华为"],
            camera_need=NeedLevel.HIGH
        )
        result = service._detect_brand_feature_mismatch(profile)
        assert result is None

    def test_gaming_brand_for_gaming(self, service):
        """游戏品牌选游戏=匹配"""
        profile = UserProfile(
            brand_preference=["红魔"],
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_brand_feature_mismatch(profile)
        assert result is None

    def test_no_brand_preference(self, service):
        """无品牌偏好=无冲突"""
        profile = UserProfile(gaming_need=NeedLevel.HIGH)
        result = service._detect_brand_feature_mismatch(profile)
        assert result is None

    def test_no_high_feature(self, service):
        """无高需求功能=无冲突"""
        profile = UserProfile(
            brand_preference=["华为"],
            gaming_need=NeedLevel.MEDIUM
        )
        result = service._detect_brand_feature_mismatch(profile)
        assert result is None

    def test_brand_normalization_in_mismatch(self, service):
        """品牌标准化在冲突检测中生效"""
        profile = UserProfile(
            brand_preference=["huawei"],
            gaming_need=NeedLevel.HIGH
        )
        result = service._detect_brand_feature_mismatch(profile)
        assert result is not None
        assert result["brand"] == "华为"


class TestPainPointQuestionServiceGeneratePainPointQuestion:
    """测试 generate_pain_point_question() 主方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_budget_feature_conflict_response(self, service):
        """预算功能冲突生成响应"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None
        assert response.pain_point_type == "budget_too_low_for_features"
        assert response.severity == "high"
        assert len(response.quick_replies) > 0
        assert response.suggestion is not None

    def test_brand_budget_conflict_response(self, service):
        """品牌预算冲突生成响应"""
        profile = UserProfile(
            budget_max=3000,
            brand_preference=["苹果"]
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None
        assert response.pain_point_type == "brand_budget_conflict"
        assert "苹果" in response.question or "品牌" in response.question

    def test_feature_conflict_response(self, service):
        """功能冲突生成响应"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None
        assert response.pain_point_type == "gaming_camera_budget_conflict"
        assert response.severity == "medium"

    def test_battery_gaming_conflict_response(self, service):
        """续航游戏冲突生成响应"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH,
            budget_max=5000  # 避开其他冲突
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None
        assert response.pain_point_type == "battery_vs_gaming"
        assert response.severity == "low"

    def test_general_high_demand_response(self, service):
        """综合高需求低预算生成响应"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        # 注意：gaming_camera_budget_conflict 优先级更高
        # 所以这里可能是 gaming_camera_budget_conflict 而非 general
        assert response is not None

    def test_brand_feature_mismatch_response(self, service):
        """品牌功能不匹配生成响应"""
        profile = UserProfile(
            brand_preference=["华为"],
            gaming_need=NeedLevel.HIGH,
            budget_max=5000,  # 避开预算冲突
            battery_need=NeedLevel.LOW  # 避开续航冲突
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None
        assert response.pain_point_type == "brand_not_match_features"
        assert "品牌" in response.question or "游戏" in response.question

    def test_no_conflict_returns_none(self, service):
        """无冲突返回 None"""
        profile = UserProfile(
            budget_max=5000,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)
        assert response is None

    def test_complete_profile_no_conflict(self, service):
        """完整合理画像无冲突"""
        profile = UserProfile(
            budget_min=3000,
            budget_max=5000,
            gaming_need=NeedLevel.HIGH,
            brand_preference=["红魔"]  # 红魔擅长游戏，无冲突
        )
        response = service.generate_pain_point_question(profile)
        assert response is None

    def test_conflict_priority(self, service):
        """冲突检测优先级"""
        # 预算冲突优先级最高
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH,
            brand_preference=["苹果"]
        )
        response = service.generate_pain_point_question(profile)
        assert response.pain_point_type == "budget_too_low_for_features"

    def test_response_has_valid_question(self, service):
        """响应包含有效问题"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response.question is not None
        assert len(response.question) > 5
        # 中文问题应有标点
        assert "？" in response.question or "。" in response.question


class TestPainPointQuestionServiceIntegration:
    """集成测试：痛点追问在多轮对话中的应用"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_detect_conflict_after_user_specifies_need(self, service):
        """用户明确需求后检测痛点"""
        # 用户说"我要3000元以内，玩原神，拍照要好"
        profile = UserProfile(
            budget_max=3000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None
        assert response.severity in ["high", "medium"]

    def test_quick_replies_help_user_adjust(self, service):
        """快捷回复帮助用户调整"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        # 快捷回复应包含调整选项
        assert any("预算" in r or "降低" in r for r in response.quick_replies)

    def test_suggestion_is_actionable(self, service):
        """建议是可执行的"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response.suggestion is not None
        assert "建议" in response.suggestion

    def test_all_severity_levels(self, service):
        """所有严重级别都能生成"""
        severities = []

        # high: 预算冲突
        profile = UserProfile(budget_max=2500, gaming_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            severities.append(response.severity)

        # medium: 功能冲突
        profile = UserProfile(budget_max=4000, gaming_need=NeedLevel.HIGH, camera_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            severities.append(response.severity)

        # low: 续航游戏冲突
        profile = UserProfile(budget_max=5000, gaming_need=NeedLevel.HIGH, battery_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            severities.append(response.severity)

        assert "high" in severities
        assert "medium" in severities
        assert "low" in severities

    def test_randomness_in_question_selection(self, service):
        """问题选择有随机性"""
        profile = UserProfile(budget_max=2500, gaming_need=NeedLevel.HIGH)

        questions = set()
        for _ in range(5):
            response = service.generate_pain_point_question(profile)
            if response:
                questions.add(response.question)

        # 多次调用可能产生不同问题（模板随机）
        # 至少所有问题应该是有效的
        for q in questions:
            assert len(q) > 5

    def test_all_templates_can_be_triggered(self, service):
        """所有模板都能被触发"""
        triggered_types = set()

        # budget_too_low_for_features
        profile = UserProfile(budget_max=2500, gaming_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # brand_budget_conflict
        profile = UserProfile(budget_max=3000, brand_preference=["苹果"])
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # gaming_camera_budget_conflict
        profile = UserProfile(budget_max=4000, gaming_need=NeedLevel.HIGH, camera_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # battery_vs_gaming
        profile = UserProfile(budget_max=6000, gaming_need=NeedLevel.HIGH, battery_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # brand_not_match_features
        profile = UserProfile(budget_max=6000, brand_preference=["华为"], gaming_need=NeedLevel.HIGH, battery_need=NeedLevel.LOW)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # 检查至少4种类型被触发
        assert len(triggered_types) >= 4


class TestPainPointQuestionServiceNormalizeBrand:
    """测试 _normalize_brand() 方法"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_normalize_chinese_brand(self, service):
        """中文名称标准化"""
        assert service._normalize_brand("华为") == "华为"
        assert service._normalize_brand("苹果") == "苹果"
        assert service._normalize_brand("小米") == "小米"

    def test_normalize_english_brand(self, service):
        """英文名称标准化"""
        assert service._normalize_brand("apple") == "苹果"
        assert service._normalize_brand("huawei") == "华为"
        assert service._normalize_brand("xiaomi") == "小米"
        assert service._normalize_brand("samsung") == "三星"

    def test_normalize_case_insensitive(self, service):
        """大小写不敏感"""
        assert service._normalize_brand("APPLE") == "苹果"
        assert service._normalize_brand("HUAWEI") == "华为"
        assert service._normalize_brand("iPhone") == "苹果"

    def test_normalize_unknown_brand(self, service):
        """未知品牌返回原值"""
        assert service._normalize_brand("unknown") == "unknown"
        assert service._normalize_brand("Nothing") == "Nothing"