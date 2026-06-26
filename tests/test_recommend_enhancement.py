"""
测试推荐解释增强功能 (SUB-001)

验收标准：
- RECOMMEND_PROMPT模板包含【用户需求引用】板块
- RECOMMEND_PROMPT模板包含【潜在不足】板块
- _format_phone方法将pros/cons字段加入格式化输出
- Phone模型包含pros/cons字段
"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.domain import Phone
from backend.services.recommend import RECOMMEND_PROMPT, RecommendService


class TestRecommendPromptEnhancement:
    """测试 RECOMMEND_PROMPT 模板增强"""

    def test_prompt_contains_user_quote_section(self):
        """RECOMMEND_PROMPT 必须包含【用户需求引用】板块"""
        assert "用户需求引用" in RECOMMEND_PROMPT, \
            "RECOMMEND_PROMPT 缺少【用户需求引用】板块"

    def test_prompt_contains_disadvantage_section(self):
        """RECOMMEND_PROMPT 必须包含【潜在不足】板块"""
        # 检查多种可能的表述
        has_cons_section = (
            "潜在不足" in RECOMMEND_PROMPT or
            "缺点" in RECOMMEND_PROMPT or
            "不足" in RECOMMEND_PROMPT
        )
        assert has_cons_section, \
            "RECOMMEND_PROMPT 缺少【潜在不足】相关板块"

    def test_prompt_requires_quote_user_words(self):
        """RECOMMEND_PROMPT 必须要求引用用户原话"""
        assert "引用用户原话" in RECOMMEND_PROMPT or "引用用户" in RECOMMEND_PROMPT, \
            "RECOMMEND_PROMPT 缺少引用用户原话的要求"

    def test_prompt_requires_expose_disadvantages(self):
        """RECOMMEND_PROMPT 必须要求暴露缺点"""
        assert "暴露缺点" in RECOMMEND_PROMPT or "缺点" in RECOMMEND_PROMPT or "不足" in RECOMMEND_PROMPT, \
            "RECOMMEND_PROMPT 缺少暴露缺点的要求"


class TestPhoneModelProsCons:
    """测试 Phone 模型的 pros/cons 字段"""

    def test_phone_model_has_pros_column(self):
        """Phone 模型必须有 pros 字段定义"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            pros='["性能强劲", "续航优秀"]'
        )
        assert hasattr(phone, 'pros'), "Phone 模型缺少 pros 字段"
        assert phone.pros == '["性能强劲", "续航优秀"]'

    def test_phone_model_has_cons_column(self):
        """Phone 模型必须有 cons 字段定义"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            cons='["价格较高", "重量较大"]'
        )
        assert hasattr(phone, 'cons'), "Phone 模型缺少 cons 字段"
        assert phone.cons == '["价格较高", "重量较大"]'

    def test_phone_to_dict_parses_pros_json(self):
        """Phone.to_dict() 必须解析 pros JSON 数组"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            pros='["性能强劲", "续航优秀"]'
        )
        result = phone.to_dict()
        assert "pros" in result
        assert isinstance(result["pros"], list)
        assert result["pros"] == ["性能强劲", "续航优秀"]

    def test_phone_to_dict_parses_cons_json(self):
        """Phone.to_dict() 必须解析 cons JSON 数组"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            cons='["价格较高", "重量较大"]'
        )
        result = phone.to_dict()
        assert "cons" in result
        assert isinstance(result["cons"], list)
        assert result["cons"] == ["价格较高", "重量较大"]

    def test_phone_to_dict_handles_null_pros(self):
        """Phone.to_dict() 必须处理 pros 为 None 的情况"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            pros=None
        )
        result = phone.to_dict()
        assert "pros" in result
        assert result["pros"] == []

    def test_phone_to_dict_handles_null_cons(self):
        """Phone.to_dict() 必须处理 cons 为 None 的情况"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            cons=None
        )
        result = phone.to_dict()
        assert "cons" in result
        assert result["cons"] == []

    def test_phone_to_dict_handles_invalid_json_pros(self):
        """Phone.to_dict() 必须处理 pros 无效 JSON 的情况"""
        phone = Phone(
            brand="测试品牌",
            model="测试型号",
            price=3999,
            pros="这不是有效的JSON"
        )
        result = phone.to_dict()
        assert "pros" in result
        assert result["pros"] == []


class TestFormatPhoneProsCons:
    """测试 _format_phone 方法对 pros/cons 的处理"""

    def test_format_phone_includes_pros(self):
        """_format_phone 必须将 pros 加入格式化输出"""
        service = RecommendService()
        phone = Phone(
            brand="小米",
            model="14 Pro",
            price=4999,
            processor="骁龙8 Gen3",
            pros='["性能强劲", "徕卡影像"]'
        )
        result = service._format_phone(phone)
        assert "优点" in result
        assert "性能强劲" in result
        assert "徕卡影像" in result

    def test_format_phone_includes_cons(self):
        """_format_phone 必须将 cons 加入格式化输出"""
        service = RecommendService()
        phone = Phone(
            brand="小米",
            model="14 Pro",
            price=4999,
            processor="骁龙8 Gen3",
            cons='["价格较高", "重量较大"]'
        )
        result = service._format_phone(phone)
        assert "缺点" in result
        assert "价格较高" in result
        assert "重量较大" in result

    def test_format_phone_includes_both_pros_and_cons(self):
        """_format_phone 必须同时包含 pros 和 cons"""
        service = RecommendService()
        phone = Phone(
            brand="vivo",
            model="X100 Pro",
            price=4999,
            processor="天玑9300",
            pros='["影像出色", "快充快"]',
            cons='["系统广告多"]'
        )
        result = service._format_phone(phone)
        assert "优点" in result
        assert "缺点" in result
        assert "影像出色" in result
        assert "系统广告多" in result

    def test_format_phone_handles_empty_pros_cons(self):
        """_format_phone 必须处理空的 pros/cons"""
        service = RecommendService()
        phone = Phone(
            brand="小米",
            model="14",
            price=3999,
            pros='[]',
            cons='[]'
        )
        result = service._format_phone(phone)
        # 空数组不应显示优点/缺点标签
        assert "优点:" not in result
        assert "缺点:" not in result

    def test_format_phone_handles_none_pros_cons(self):
        """_format_phone 必须处理 None 的 pros/cons"""
        service = RecommendService()
        phone = Phone(
            brand="小米",
            model="14",
            price=3999,
            pros=None,
            cons=None
        )
        result = service._format_phone(phone)
        # None 不应显示优点/缺点标签
        assert "优点:" not in result
        assert "缺点:" not in result


class TestRecommendServiceIntegration:
    """测试 RecommendService 集成功能"""

    def test_recommend_service_format_phone_complete(self):
        """测试完整的手机格式化输出"""
        service = RecommendService()
        phone = Phone(
            brand="小米",
            model="14 Ultra",
            price=5999,
            processor="骁龙8 Gen3",
            ram=16,
            storage=512,
            camera_main=5000,
            battery=5000,
            features='["徕卡影像", "潜望长焦"]',
            suitable_for='["摄影爱好者", "商务人士"]',
            pros='["影像顶级", "续航优秀"]',
            cons='["价格较高", "重量大"]'
        )
        result = service._format_phone(phone)

        # 验证所有字段都被包含
        assert "小米 14 Ultra" in result
        assert "5999元" in result
        assert "骁龙8 Gen3" in result
        assert "徕卡影像" in result
        assert "摄影爱好者" in result
        assert "优点" in result
        assert "影像顶级" in result
        assert "缺点" in result
        assert "价格较高" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
