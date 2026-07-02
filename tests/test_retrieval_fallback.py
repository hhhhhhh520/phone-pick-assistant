"""测试分级回退检索 search_with_fallback (ISSUE-036/039)

核心场景:
1. 拍照+预算场景命中 → tier-1 正常返回，无告警
2. 拍照场景过滤为空但预算内有机型 → tier-2 保留预算+场景排序，发告警
3. 预算+品牌过滤后全空 → tier-3 返回空 + 告警
4. 无预算的拍照请求 → tier-2 不触发"预算空"误告警
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.domain import Phone, Base
from backend.services.retrieval import RetrievalService
from backend.models.schemas import IntentResult, IntentType


@pytest.fixture
def db_session():
    """测试数据库：含拍照旗舰（带影像标签）和普通预算内机型（无影像标签）"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    test_phones = [
        # 拍照旗舰（命中"影像"关键词），5000档
        Phone(
            brand="小米", model="小米14 Ultra", price=6499,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5300, camera_main=5000,
            features='["徕卡影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/mi14u.jpg",
        ),
        # 5000档普通旗舰，无影像标签（用于 tier-2 放宽场景测试）
        Phone(
            brand="小米", model="小米15", price=4999,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=5000, camera_main=5000,
            features='["高刷屏", "旗舰芯片"]',
            suitable_for='[]',
            image_url="http://example.com/mi15.jpg",
        ),
        Phone(
            brand="华为", model="Mate 70", price=4999,
            processor="麒麟9020", ram=12, storage=256,
            battery=5500, camera_main=5000,
            features='["高刷屏", "旗舰芯片"]',
            suitable_for='[]',
            image_url="http://example.com/mate70.jpg",
        ),
        # 入门机（1000元档，不应出现在5000预算推荐中）
        Phone(
            brand="红米", model="Redmi Note", price=999,
            processor="天玑6020", ram=6, storage=128,
            battery=5000, camera_main=5000,
            features='["大屏"]',
            suitable_for='[]',
            image_url="http://example.com/note.jpg",
        ),
    ]
    db.add_all(test_phones)
    db.commit()
    yield db
    db.close()


class TestSearchWithFallback:
    """测试 search_with_fallback 分级回退"""

    def test_tier1_normal_match_no_notice(self, db_session):
        """tier-1: 拍照旗舰命中影像关键词 → 正常返回，无告警"""
        service = RetrievalService(db_session)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=4000, budget_max=7000,
            features=["拍照"],
        )
        phones, notice = service.search_with_fallback(intent, limit=5)

        assert len(phones) > 0
        assert notice is None
        # 应命中拍照旗舰而非入门机
        models = [p.model for p in phones]
        assert "小米14 Ultra" in models
        assert "Redmi Note" not in models

    def test_tier2_relax_scenario_keep_budget(self, db_session):
        """tier-2: 拍照过滤为空但预算内有机型 → 保留预算，发告警，不返回入门机

        模拟 ISSUE-036 核心场景：5000预算拍照，若无影像旗舰则不应推 999 元入门机
        """
        service = RetrievalService(db_session)
        # 预算限定 4000-5500，此区间内只有小米15/Mate70（无影像标签）
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=4000, budget_max=5500,
            features=["拍照"],
        )
        phones, notice = service.search_with_fallback(intent, limit=5)

        # tier-2 应返回预算内机型
        assert len(phones) > 0
        # 关键：不返回入门机（保留预算过滤）
        for p in phones:
            assert p.price >= 4000, f"tier-2 不应返回预算外机型: {p.model} {p.price}"
            assert p.price <= 5500
        # 应有告警提示
        assert notice is not None
        assert "拍照" in notice or "未找到" in notice

    def test_tier3_no_data_in_budget(self, db_session):
        """tier-3: 预算+品牌过滤后全空 → 返回空 + 告警"""
        service = RetrievalService(db_session)
        # 预算 100000-200000，库里无此价位机型
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=100000, budget_max=200000,
            features=["拍照"],
        )
        phones, notice = service.search_with_fallback(intent, limit=5)

        assert phones == []
        assert notice is not None
        assert "暂无" in notice or "调整" in notice

    def test_tier2_no_budget_no_false_alarm(self, db_session):
        """tier-2: 无预算的拍照请求 → 不触发"预算空"误告警

        用户只说"推荐拍照手机"无预算，budget_min=0/budget_max=100000，
        此时 tier-2 命中全库不应报"该价位暂无机型"
        """
        service = RetrievalService(db_session)
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0, budget_max=100000,
            features=["拍照"],
        )
        phones, notice = service.search_with_fallback(intent, limit=5)
        # 应有拍照旗舰命中（tier-1）
        assert len(phones) > 0
        assert notice is None

    def test_tier2_notice_no_budget_no_price_word(self, db_session):
        """tier-2 无预算时 notice 不应出现"该价位"字样 (ISSUE-036 误报修正)

        构造无预算 + 场景过滤为空的场景：tier-2 命中但 notice 应说"当前"而非"该价位"
        """
        service = RetrievalService(db_session)
        # 无线充电场景：库里无此特性的机型，但 tier-2 放宽后命中其他机型
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0, budget_max=100000,
            features=["无线充电"],
        )
        phones, notice = service.search_with_fallback(intent, limit=5)
        # tier-2 应命中（无场景标签的机型）
        assert len(phones) > 0
        if notice is not None:
            # 无预算时不应出现"该价位"
            assert "该价位" not in notice, f"无预算时 notice 不应提'该价位'：{notice}"

    def test_tier3_notice_scoped_by_filter(self, db_session):
        """tier-3 告警文案应按实际过滤维度措辞 (ISSUE-036)

        无预算 + 无品牌 → "暂无机型数据，请调整筛选条件"
        有预算 + 无品牌 → "该价位暂无机型数据，请调整预算"
        """
        service = RetrievalService(db_session)
        # 无预算无品牌，超高价位无人（用 brand 制造空集）
        intent_brand = IntentResult(
            intent=IntentType.RECOMMEND,
            budget_min=0, budget_max=100000,
            brands=["不存在的品牌"],
            features=["拍照"],
        )
        phones, notice = service.search_with_fallback(intent_brand, limit=5)
        assert phones == []
        assert notice is not None
        assert "该品牌" in notice
