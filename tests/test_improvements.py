"""
P0/P1/P2 改进项集成测试与验收

本测试文件验证以下改进项的端到端功能：

P0 (SUB-001): 推荐解释增强
  - 推荐包含用户原话引用
  - 推荐包含潜在不足/缺点

P1 (SUB-002/003/004): 体验标签库
  - feature_tags.py 定义标签
  - fill_tags.py 填充数据库
  - retrieval.py 标签筛选

P2 (SUB-005/006): 痛点追问机制
  - PainPointQuestionService 检测痛点
  - 生成针对性追问
"""
import pytest
import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.domain import Phone, Base
from backend.models.schemas import IntentResult, IntentType, UserProfile, NeedLevel
from backend.services.recommend import RECOMMEND_PROMPT, RecommendService
from backend.services.retrieval import RetrievalService
from backend.services.question import PainPointQuestionService, PainPointResponse
from backend.data.feature_tags import (
    FEATURE_TAGS,
    SUITABLE_FOR_TAGS,
    get_feature_tag_names,
    get_suitable_for_tag_names,
    find_matching_feature_tags,
    find_matching_suitable_for_tags,
    suggest_tags_from_text,
    validate_tags,
    get_tag_statistics
)


# ============================================================
# P0: 推荐解释增强测试
# ============================================================

class TestRecommendationQuote:
    """测试推荐包含用户原话引用 (P0)"""

    def test_prompt_has_user_quote_section(self):
        """RECOMMEND_PROMPT 必须包含用户需求引用板块"""
        assert "用户需求引用" in RECOMMEND_PROMPT, \
            "RECOMMEND_PROMPT 缺少【用户需求引用】板块"

    def test_prompt_requires_quote_user_words(self):
        """RECOMMEND_PROMPT 必须要求引用用户原话"""
        assert "引用用户原话" in RECOMMEND_PROMPT or "引用用户" in RECOMMEND_PROMPT, \
            "RECOMMEND_PROMPT 缺少引用用户原话的要求"

    def test_prompt_has_quote_example(self):
        """RECOMMEND_PROMPT 应包含引用格式示例"""
        # 检查是否有引号引用的示例说明
        has_quote_example = (
            ('"' in RECOMMEND_PROMPT and '用户提到' in RECOMMEND_PROMPT) or
            ('引用' in RECOMMEND_PROMPT and '需求' in RECOMMEND_PROMPT)
        )
        assert has_quote_example, \
            "RECOMMEND_PROMPT 应包含引用格式示例"


class TestRecommendationCons:
    """测试推荐包含缺点 (P0)"""

    def test_prompt_has_disadvantage_section(self):
        """RECOMMEND_PROMPT 必须包含潜在不足板块"""
        has_cons_section = (
            "潜在不足" in RECOMMEND_PROMPT or
            "缺点" in RECOMMEND_PROMPT or
            "不足" in RECOMMEND_PROMPT
        )
        assert has_cons_section, \
            "RECOMMEND_PROMPT 缺少【潜在不足】相关板块"

    def test_prompt_requires_expose_disadvantages(self):
        """RECOMMEND_PROMPT 必须要求暴露缺点"""
        assert "暴露缺点" in RECOMMEND_PROMPT or "缺点" in RECOMMEND_PROMPT, \
            "RECOMMEND_PROMPT 缺少暴露缺点的要求"

    def test_format_phone_includes_cons(self):
        """_format_phone 方法必须将 cons 加入格式化输出"""
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


# ============================================================
# P1: 标签筛选功能测试
# ============================================================

@pytest.fixture
def tag_test_db():
    """创建标签测试数据库"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    test_phones = [
        # 游戏手机
        Phone(
            brand="iQOO", model="iQOO 12", price=3999,
            processor="骁龙8 Gen3", ram=16, storage=256,
            battery=5000, charging_wired=120,
            camera_main=5000,
            features='["游戏手机", "电竞", "高刷屏"]',
            suitable_for='["游戏玩家"]',
            image_url="http://example.com/iqoo12.jpg"
        ),
        Phone(
            brand="红魔", model="红魔9 Pro", price=4999,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=6500, charging_wired=80,
            camera_main=5000,
            features='["游戏手机", "电竞散热"]',
            suitable_for='["游戏玩家"]',
            image_url="http://example.com/n9pro.jpg"
        ),
        # 拍照手机
        Phone(
            brand="小米", model="小米14 Ultra", price=6499,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5300, charging_wired=90,
            camera_main=5000,
            features='["徕卡影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/mi14ultra.jpg"
        ),
        Phone(
            brand="OPPO", model="Find X7 Ultra", price=5999,
            processor="天玑9300", ram=16, storage=256,
            battery=5000, charging_wired=100,
            camera_main=5000,
            features='["哈苏影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/findx7.jpg"
        ),
        # 续航手机
        Phone(
            brand="vivo", model="vivo Y200", price=1999,
            processor="骁龙6 Gen1", ram=8, storage=256,
            battery=6000, charging_wired=44,
            camera_main=5000,
            features='["大电池", "长续航"]',
            suitable_for='["续航需求"]',
            image_url="http://example.com/y200.jpg"
        ),
        # 无标签手机
        Phone(
            brand="小米", model="小米14", price=3999,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=4610, charging_wired=90, charging_wireless=50,
            camera_main=5000,
            features='["小屏旗舰"]',
            suitable_for='["小屏党"]',
            image_url="http://example.com/mi14.jpg"
        ),
    ]

    db.add_all(test_phones)
    db.commit()
    yield db
    db.close()


class TestTagFiltering:
    """测试标签筛选功能 (P1)"""

    def test_feature_tags_defined(self):
        """特性标签库必须定义"""
        assert len(FEATURE_TAGS) > 0, "FEATURE_TAGS 不应为空"
        # 必须包含核心标签
        assert "游戏手机" in FEATURE_TAGS
        assert "徕卡影像" in FEATURE_TAGS
        assert "快充" in FEATURE_TAGS
        assert "大电池" in FEATURE_TAGS

    def test_suitable_for_tags_defined(self):
        """适用人群标签库必须定义"""
        assert len(SUITABLE_FOR_TAGS) > 0, "SUITABLE_FOR_TAGS 不应为空"
        # 必须包含核心标签
        assert "游戏玩家" in SUITABLE_FOR_TAGS
        assert "摄影爱好者" in SUITABLE_FOR_TAGS

    def test_tag_validation(self):
        """标签定义必须完整"""
        result = validate_tags()
        assert result["valid"], f"标签验证失败: {result['errors']}"

    def test_gaming_filter_returns_gaming_phones(self, tag_test_db):
        """游戏场景筛选应返回游戏手机"""
        service = RetrievalService(tag_test_db)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=10)

        # 应该返回手机
        assert len(phones) > 0, "游戏场景应返回手机"

        # 所有返回的手机都应有游戏相关标签
        for phone in phones:
            has_gaming_tag = (
                (phone.features and ("游戏" in phone.features or "电竞" in phone.features)) or
                (phone.suitable_for and "游戏玩家" in phone.suitable_for)
            )
            assert has_gaming_tag, f"游戏场景返回了无游戏标签的手机: {phone.model}"

    def test_camera_filter_returns_camera_phones(self, tag_test_db):
        """拍照场景筛选应返回影像旗舰"""
        service = RetrievalService(tag_test_db)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=10)

        assert len(phones) > 0, "拍照场景应返回手机"

        # 所有返回的手机都应有影像标签
        camera_features = ["徕卡", "哈苏", "蔡司"]
        for phone in phones:
            has_camera_tag = (
                (phone.features and any(f in phone.features for f in camera_features)) or
                (phone.suitable_for and "摄影爱好者" in phone.suitable_for)
            )
            assert has_camera_tag, f"拍照场景返回了无影像标签的手机: {phone.model}"

    def test_battery_filter_returns_battery_phones(self, tag_test_db):
        """续航场景筛选应返回大电池手机"""
        service = RetrievalService(tag_test_db)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=10)

        assert len(phones) > 0, "续航场景应返回手机"

        # 所有返回的手机都应有续航标签或电池>=5000
        battery_features = ["大电池", "快充"]
        for phone in phones:
            has_battery_tag = (
                (phone.features and any(f in phone.features for f in battery_features)) or
                (phone.suitable_for and "续航" in phone.suitable_for) or
                (phone.battery and phone.battery >= 5000)
            )
            assert has_battery_tag, f"续航场景返回了无续航标签的手机: {phone.model}"

    def test_tag_suggestion_from_text(self):
        """从用户文本提取标签建议"""
        # 游戏相关
        tags = suggest_tags_from_text("我要玩原神，需要游戏手机")
        assert "游戏手机" in tags, f"应识别游戏标签，实际: {tags}"

        # 拍照相关
        tags = suggest_tags_from_text("拍照要好，喜欢徕卡")
        assert "徕卡影像" in tags, f"应识别徕卡标签，实际: {tags}"

        # 续航相关
        tags = suggest_tags_from_text("续航要长，大电池")
        assert "大电池" in tags, f"应识别大电池标签，实际: {tags}"

    def test_find_matching_feature_tags(self):
        """根据手机参数匹配特性标签"""
        # 游戏手机匹配
        phone_data = {
            "model": "iQOO 12",
            "processor": "骁龙8 Gen3",
            "features": "游戏手机"
        }
        tags = find_matching_feature_tags(phone_data)
        assert "游戏手机" in tags, f"应匹配游戏手机标签，实际: {tags}"

        # 大电池匹配
        phone_data = {
            "model": "Y200",
            "battery": 6000
        }
        tags = find_matching_feature_tags(phone_data)
        assert "大电池" in tags, f"应匹配大电池标签，实际: {tags}"


# ============================================================
# P2: 痛点追问机制测试
# ============================================================

class TestPainPointQuestion:
    """测试痛点追问触发 (P2)"""

    @pytest.fixture
    def service(self):
        return PainPointQuestionService()

    def test_budget_too_low_for_gaming(self, service):
        """预算不足+高游戏需求=痛点"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None, "应触发痛点追问"
        assert response.pain_point_type == "budget_too_low_for_features"
        assert response.severity == "high"
        assert len(response.quick_replies) > 0
        assert response.suggestion is not None

    def test_budget_too_low_for_camera(self, service):
        """预算不足+高拍照需求=痛点"""
        profile = UserProfile(
            budget_max=2500,
            camera_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None, "应触发痛点追问"
        assert response.pain_point_type == "budget_too_low_for_features"

    def test_brand_budget_conflict(self, service):
        """品牌预算冲突=痛点"""
        profile = UserProfile(
            budget_max=3000,
            brand_preference=["苹果"]
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None, "应触发品牌预算冲突"
        assert response.pain_point_type == "brand_budget_conflict"
        assert "苹果" in response.question or "品牌" in response.question

    def test_gaming_camera_budget_conflict(self, service):
        """高游戏+高拍照+预算有限=痛点"""
        profile = UserProfile(
            budget_max=4000,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None, "应触发功能冲突"
        assert response.pain_point_type == "gaming_camera_budget_conflict"
        assert response.severity == "medium"

    def test_battery_gaming_conflict(self, service):
        """高游戏+高续航=痛点（难以同时满足）"""
        profile = UserProfile(
            gaming_need=NeedLevel.HIGH,
            battery_need=NeedLevel.HIGH,
            budget_max=5000  # 避开其他冲突
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None, "应触发续航游戏冲突"
        assert response.pain_point_type == "battery_vs_gaming"
        assert response.severity == "low"

    def test_brand_feature_mismatch(self, service):
        """品牌与功能不匹配=痛点"""
        profile = UserProfile(
            brand_preference=["华为"],
            gaming_need=NeedLevel.HIGH,
            budget_max=5000,
            battery_need=NeedLevel.LOW
        )
        response = service.generate_pain_point_question(profile)

        assert response is not None, "应触发品牌功能不匹配"
        assert response.pain_point_type == "brand_not_match_features"

    def test_no_conflict_returns_none(self, service):
        """无冲突返回 None"""
        profile = UserProfile(
            budget_max=5000,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)
        assert response is None

    def test_response_has_valid_quick_replies(self, service):
        """响应包含有效快捷回复"""
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH
        )
        response = service.generate_pain_point_question(profile)

        assert len(response.quick_replies) >= 3, \
            f"应至少有3个快捷回复，实际: {len(response.quick_replies)}"

        # 快捷回复应包含调整选项
        has_adjust_option = any(
            "预算" in r or "降低" in r or "提高" in r
            for r in response.quick_replies
        )
        assert has_adjust_option, "快捷回复应包含调整选项"


# ============================================================
# 端到端集成测试
# ============================================================

class TestImprovementsIntegration:
    """P0/P1/P2 改进项端到端集成测试"""

    def test_p0_prompt_structure_complete(self):
        """P0: 推荐提示词结构完整"""
        # 用户需求引用
        assert "用户需求引用" in RECOMMEND_PROMPT
        assert "引用用户原话" in RECOMMEND_PROMPT

        # 潜在不足
        assert "潜在不足" in RECOMMEND_PROMPT
        assert "暴露缺点" in RECOMMEND_PROMPT or "缺点" in RECOMMEND_PROMPT

        # 推荐理由格式
        assert "推荐理由" in RECOMMEND_PROMPT

    def test_p1_tags_complete(self):
        """P1: 标签库完整"""
        stats = get_tag_statistics()

        # 特性标签数量
        assert stats["feature_tags_count"] >= 15, \
            f"特性标签应至少15个，实际: {stats['feature_tags_count']}"

        # 适用人群标签数量
        assert stats["suitable_for_tags_count"] >= 10, \
            f"适用人群标签应至少10个，实际: {stats['suitable_for_tags_count']}"

        # 验证标签定义
        result = validate_tags()
        assert result["valid"], f"标签验证失败: {result['errors']}"

    def test_p2_service_can_detect_all_conflicts(self):
        """P2: 痛点检测服务能检测所有冲突类型"""
        service = PainPointQuestionService()
        triggered_types = set()

        # 1. budget_too_low_for_features
        profile = UserProfile(budget_max=2500, gaming_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # 2. brand_budget_conflict
        profile = UserProfile(budget_max=3000, brand_preference=["苹果"])
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # 3. gaming_camera_budget_conflict
        profile = UserProfile(budget_max=4000, gaming_need=NeedLevel.HIGH, camera_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # 4. battery_vs_gaming
        profile = UserProfile(budget_max=6000, gaming_need=NeedLevel.HIGH, battery_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # 5. brand_not_match_features
        profile = UserProfile(
            budget_max=6000,
            brand_preference=["华为"],
            gaming_need=NeedLevel.HIGH,
            battery_need=NeedLevel.LOW
        )
        response = service.generate_pain_point_question(profile)
        if response:
            triggered_types.add(response.pain_point_type)

        # 应至少触发4种冲突类型
        assert len(triggered_types) >= 4, \
            f"应至少触发4种冲突类型，实际: {triggered_types}"

    def test_full_flow_recommend_with_quote_and_cons(self, tag_test_db):
        """完整流程：推荐包含用户需求引用和缺点"""
        # 1. 创建推荐服务
        recommend_service = RecommendService()

        # 2. 创建测试手机（带优点和缺点）
        phone = Phone(
            brand="小米",
            model="14 Ultra",
            price=5999,
            processor="骁龙8 Gen3",
            ram=16,
            storage=512,
            battery=5300,
            camera_main=5000,
            features='["徕卡影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            pros='["影像顶级", "续航优秀"]',
            cons='["价格较高", "重量大"]'
        )

        # 3. 格式化手机信息
        formatted = recommend_service._format_phone(phone)

        # 验证包含优点
        assert "优点" in formatted
        assert "影像顶级" in formatted

        # 验证包含缺点
        assert "缺点" in formatted
        assert "价格较高" in formatted

    def test_full_flow_tag_filter_then_recommend(self, tag_test_db):
        """完整流程：标签筛选后推荐"""
        # 1. 用户意图：游戏场景
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"],
            budget_min=3000,
            budget_max=5000
        )

        # 2. 标签筛选
        retrieval_service = RetrievalService(tag_test_db)
        phones = retrieval_service.search(intent, limit=5)

        # 3. 验证筛选结果
        assert len(phones) > 0, "应返回手机"

        for phone in phones:
            # 价格应在范围内
            assert 3000 <= phone.price <= 5000
            # 应有游戏标签
            has_gaming = (
                (phone.features and "游戏" in phone.features) or
                (phone.suitable_for and "游戏玩家" in phone.suitable_for)
            )
            assert has_gaming, f"应只返回游戏手机: {phone.model}"

    def test_full_flow_pain_point_guidance(self):
        """完整流程：痛点检测引导用户"""
        service = PainPointQuestionService()

        # 1. 用户画像：预算低但需求高
        profile = UserProfile(
            budget_max=2500,
            gaming_need=NeedLevel.HIGH,
            camera_need=NeedLevel.HIGH
        )

        # 2. 检测痛点
        response = service.generate_pain_point_question(profile)

        # 3. 验证痛点响应
        assert response is not None
        assert response.severity in ["high", "medium"]

        # 4. 快捷回复应帮助用户调整
        assert len(response.quick_replies) >= 3
        has_budget_option = any("预算" in r for r in response.quick_replies)
        has_demand_option = any("降低" in r or "优先" in r for r in response.quick_replies)
        assert has_budget_option or has_demand_option


# ============================================================
# 验收测试汇总
# ============================================================

class TestAcceptance:
    """验收测试：确认所有改进项完成"""

    def test_p0_acceptance(self):
        """P0 验收：推荐解释增强"""
        # 用户需求引用板块
        assert "用户需求引用" in RECOMMEND_PROMPT
        # 潜在不足板块
        assert "潜在不足" in RECOMMEND_PROMPT or "缺点" in RECOMMEND_PROMPT
        # 引用用户原话要求
        assert "引用用户原话" in RECOMMEND_PROMPT
        # 暴露缺点要求
        assert "暴露缺点" in RECOMMEND_PROMPT or "缺点" in RECOMMEND_PROMPT

    def test_p1_acceptance(self):
        """P1 验收：体验标签库"""
        # 标签定义
        assert len(FEATURE_TAGS) >= 15
        assert len(SUITABLE_FOR_TAGS) >= 10

        # 核心标签存在
        assert "游戏手机" in FEATURE_TAGS
        assert "徕卡影像" in FEATURE_TAGS
        assert "大电池" in FEATURE_TAGS
        assert "快充" in FEATURE_TAGS
        assert "游戏玩家" in SUITABLE_FOR_TAGS
        assert "摄影爱好者" in SUITABLE_FOR_TAGS

        # 标签验证通过
        result = validate_tags()
        assert result["valid"]

    def test_p2_acceptance(self):
        """P2 验收：痛点追问机制"""
        service = PainPointQuestionService()

        # 预算冲突检测
        profile = UserProfile(budget_max=2500, gaming_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        assert response is not None
        assert response.pain_point_type == "budget_too_low_for_features"

        # 品牌冲突检测
        profile = UserProfile(budget_max=3000, brand_preference=["苹果"])
        response = service.generate_pain_point_question(profile)
        assert response is not None
        assert response.pain_point_type == "brand_budget_conflict"

        # 功能冲突检测
        profile = UserProfile(budget_max=4000, gaming_need=NeedLevel.HIGH, camera_need=NeedLevel.HIGH)
        response = service.generate_pain_point_question(profile)
        assert response is not None
        assert response.pain_point_type == "gaming_camera_budget_conflict"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
