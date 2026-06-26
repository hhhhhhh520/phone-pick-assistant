"""
IntentResult 模型追问字段单元测试

测试覆盖：
- need_clarification 默认值和设置
- missing_fields 字段
- clarification_question 字段
- 向后兼容性测试
"""
import pytest
from backend.models.schemas import IntentResult, IntentType


class TestIntentResultClarificationFields:
    """测试 IntentResult 追问相关字段"""

    def test_default_need_clarification_false(self):
        """默认不需要追问"""
        intent = IntentResult(intent=IntentType.RECOMMEND)
        assert intent.need_clarification is False

    def test_default_no_need_features_empty_list(self):
        """默认不需要的功能为空列表（与其他列表字段一致）"""
        intent = IntentResult(intent=IntentType.RECOMMEND)
        assert intent.no_need_features == []

    def test_default_missing_fields_empty_list(self):
        """默认缺失字段为空列表（与其他列表字段一致）"""
        intent = IntentResult(intent=IntentType.RECOMMEND)
        assert intent.missing_fields == []

    def test_default_clarification_question_none(self):
        """默认追问问题为 None"""
        intent = IntentResult(intent=IntentType.RECOMMEND)
        assert intent.clarification_question is None

    def test_set_need_clarification_true(self):
        """设置需要追问"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            need_clarification=True
        )
        assert intent.need_clarification is True

    def test_set_missing_fields(self):
        """设置缺失字段列表"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            missing_fields=["预算范围", "品牌偏好"]
        )
        assert intent.missing_fields == ["预算范围", "品牌偏好"]

    def test_set_clarification_question(self):
        """设置追问问题"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            need_clarification=True,
            clarification_question="请问您的预算大概是多少呢？"
        )
        assert intent.clarification_question == "请问您的预算大概是多少呢？"

    def test_full_clarification_intent(self):
        """完整的追问意图"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            need_clarification=True,
            missing_fields=["预算范围", "功能需求"],
            clarification_question="请告诉我您的预算范围，以及更看重游戏性能还是拍照效果？"
        )
        assert intent.need_clarification is True
        assert len(intent.missing_fields) == 2
        assert "预算范围" in intent.missing_fields
        assert intent.clarification_question is not None


class TestIntentResultBackwardCompatibility:
    """测试向后兼容性"""

    def test_existing_code_still_works(self):
        """现有代码不受影响"""
        # 原有创建方式仍然有效
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=2000,
            budget_max=4000,
            brands=["小米"],
            features=["游戏"]
        )
        assert intent.intent == IntentType.RECOMMEND
        assert intent.budget_min == 2000
        assert intent.budget_max == 4000
        assert intent.brands == ["小米"]
        assert intent.features == ["游戏"]
        # 新字段使用默认值
        assert intent.need_clarification is False
        assert intent.missing_fields == []
        assert intent.clarification_question is None

    def test_mixed_old_and_new_fields(self):
        """混合使用旧字段和新字段"""
        intent = IntentResult(
            intent=IntentType.COMPARE,
            budget_min=3000,
            budget_max=5000,
            brands=["华为", "小米"],
            need_clarification=True,
            missing_fields=["具体机型"]
        )
        assert intent.intent == IntentType.COMPARE
        assert intent.budget_min == 3000
        assert intent.need_clarification is True
        assert intent.missing_fields == ["具体机型"]


class TestIntentResultJSONSerialization:
    """测试 JSON 序列化"""

    def test_model_dump_includes_new_fields(self):
        """model_dump 包含新字段"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            need_clarification=True,
            missing_fields=["预算"],
            clarification_question="预算多少？"
        )
        data = intent.model_dump()
        assert "need_clarification" in data
        assert data["need_clarification"] is True
        assert data["missing_fields"] == ["预算"]
        assert data["clarification_question"] == "预算多少？"

    def test_model_dump_defaults(self):
        """model_dump 包含默认值"""
        intent = IntentResult(intent=IntentType.RECOMMEND)
        data = intent.model_dump()
        assert data["need_clarification"] is False
        assert data["missing_fields"] == []
        assert data["clarification_question"] is None


class TestIntentResultValidation:
    """测试字段验证"""

    def test_all_list_fields_default_to_empty_list(self):
        """所有列表字段默认值应为空列表，保持一致性"""
        intent = IntentResult(intent=IntentType.RECOMMEND)
        # 这些字段都应该默认为空列表
        assert intent.brands == []
        assert intent.features == []
        assert intent.phones_mentioned == []
        assert intent.no_need_features == []
        assert intent.missing_fields == []

    def test_empty_missing_fields_allowed(self):
        """缺失字段可以是空列表"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            need_clarification=False,
            missing_fields=[]
        )
        assert intent.missing_fields == []

    def test_clarification_without_missing_fields(self):
        """可以只设置追问问题，不设置缺失字段"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            need_clarification=True,
            clarification_question="请问您有什么品牌偏好吗？"
        )
        assert intent.need_clarification is True
        assert intent.missing_fields == []
        assert intent.clarification_question is not None

    def test_intent_type_enum_still_works(self):
        """IntentType 枚举仍然正常工作"""
        recommend = IntentResult(intent=IntentType.RECOMMEND)
        compare = IntentResult(intent=IntentType.COMPARE)
        filter_intent = IntentResult(intent=IntentType.FILTER)

        assert recommend.intent == IntentType.RECOMMEND
        assert compare.intent == IntentType.COMPARE
        assert filter_intent.intent == IntentType.FILTER
