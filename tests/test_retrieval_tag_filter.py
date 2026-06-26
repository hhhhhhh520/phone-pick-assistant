"""测试检索服务标签匹配功能

测试场景:
1. 游戏场景筛选 features 包含 '游戏' 或 '电竞' 的手机
2. 拍照场景筛选 features 包含 '徕卡'/'哈苏'/'蔡司' 或 suitable_for 包含 '摄影爱好者'
3. 续航场景筛选 features 包含 '大电池' 或 '快充'
4. 多场景组合筛选
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
    """创建测试数据库，包含标签测试数据"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    test_phones = [
        # ========== 游戏标签测试 ==========
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
        Phone(
            brand="ROG", model="ROG Phone 8", price=5999,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5500, charging_wired=65,
            camera_main=5000,
            features='["电竞", "游戏手机"]',
            suitable_for='["游戏玩家"]',
            image_url="http://example.com/rog8.jpg"
        ),

        # ========== 拍照标签测试 ==========
        Phone(
            brand="小米", model="小米14 Ultra", price=6499,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5300, charging_wired=90,
            camera_main=5000, camera_ultra=5000, camera_telephoto=12000,
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
        Phone(
            brand="vivo", model="vivo X100 Ultra", price=6499,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5500, charging_wired=80,
            camera_main=5000,
            features='["蔡司影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/x100ultra.jpg"
        ),
        Phone(
            brand="华为", model="P60 Pro", price=5988,
            processor="骁龙8+ Gen1", ram=8, storage=256,
            battery=4815, charging_wired=88,
            camera_main=4800,
            features='["XMAGE影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/p60pro.jpg"
        ),

        # ========== 续航标签测试 ==========
        Phone(
            brand="vivo", model="vivo Y200", price=1999,
            processor="骁龙6 Gen1", ram=8, storage=256,
            battery=6000, charging_wired=44,
            camera_main=5000,
            features='["大电池", "长续航"]',
            suitable_for='["续航需求"]',
            image_url="http://example.com/y200.jpg"
        ),
        Phone(
            brand="荣耀", model="荣耀Play9T", price=1399,
            processor="骁龙695", ram=8, storage=256,
            battery=6000, charging_wired=35,
            camera_main=5000,
            features='["大电池", "大音量"]',
            suitable_for='["长辈", "续航需求"]',
            image_url="http://example.com/play9t.jpg"
        ),
        Phone(
            brand="Redmi", model="Redmi Note 13 Pro+", price=1899,
            processor="天玑7200", ram=12, storage=256,
            battery=5000, charging_wired=120,
            camera_main=20000,
            features='["快充", "高像素"]',
            suitable_for='["学生"]',
            image_url="http://example.com/note13pro.jpg"
        ),

        # ========== 无标签手机 ==========
        Phone(
            brand="小米", model="小米14", price=3999,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=4610, charging_wired=90, charging_wireless=50,
            camera_main=5000,
            features='["小屏旗舰"]',
            suitable_for='["小屏党"]',
            image_url="http://example.com/mi14.jpg"
        ),
        Phone(
            brand="Redmi", model="Redmi Note 13", price=1199,
            processor="天玑6020", ram=6, storage=128,
            battery=5000, charging_wired=33,
            camera_main=10800,
            features='[]',
            suitable_for='[]',
            image_url="http://example.com/note13.jpg"
        ),
    ]

    db.add_all(test_phones)
    db.commit()
    yield db
    db.close()


class TestGamingTagFilter:
    """测试游戏场景标签筛选"""

    def test_gaming_filters_by_features_tag(self, db_session):
        """测试游戏场景筛选 features 包含'游戏'或'电竞'的手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=10)

        # 断言1: 应该返回手机
        assert len(phones) > 0, "游戏场景应返回手机"

        # 断言2: 所有返回的手机都应有游戏相关标签
        for phone in phones:
            has_gaming_tag = (
                (phone.features and ("游戏" in phone.features or "电竞" in phone.features)) or
                (phone.suitable_for and "游戏玩家" in phone.suitable_for)
            )
            assert has_gaming_tag, f"游戏场景返回了无游戏标签的手机: {phone.model}"

    def test_gaming_includes_iqoo_and_redmagic(self, db_session):
        """测试游戏场景应包含 iQOO 和红魔等游戏手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=10)
        models = [p.model for p in phones]

        # 应包含游戏手机
        gaming_models = ["iQOO 12", "红魔9 Pro", "ROG Phone 8"]
        found_count = sum(1 for m in gaming_models if m in models)
        assert found_count >= 2, f"应至少包含两款游戏手机，实际: {models}"

    def test_gaming_excludes_non_gaming_phones(self, db_session):
        """测试游戏场景排除无游戏标签的手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=10)
        models = [p.model for p in phones]

        # 无标签手机不应出现
        non_gaming_models = ["Redmi Note 13", "vivo Y200", "Redmi Note 13 Pro+"]
        for model in non_gaming_models:
            assert model not in models, f"游戏场景不应返回无游戏标签的手机: {model}"


class TestCameraTagFilter:
    """测试拍照场景标签筛选"""

    def test_camera_filters_by_brand_tags(self, db_session):
        """测试拍照场景筛选 features 包含徕卡/哈苏/蔡司的手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=10)

        # 断言1: 应该返回手机
        assert len(phones) > 0, "拍照场景应返回手机"

        # 断言2: 所有返回的手机都应有影像标签或摄影爱好者标签
        camera_features = ["徕卡", "哈苏", "蔡司"]
        for phone in phones:
            has_camera_tag = (
                (phone.features and any(f in phone.features for f in camera_features)) or
                (phone.suitable_for and "摄影爱好者" in phone.suitable_for)
            )
            assert has_camera_tag, f"拍照场景返回了无影像标签的手机: {phone.model}"

    def test_camera_includes_premium_phones(self, db_session):
        """测试拍照场景应包含小米14 Ultra、Find X7 Ultra 等影像旗舰"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=10)
        models = [p.model for p in phones]

        # 应包含影像旗舰
        camera_models = ["小米14 Ultra", "Find X7 Ultra", "vivo X100 Ultra", "P60 Pro"]
        found_count = sum(1 for m in camera_models if m in models)
        assert found_count >= 2, f"应至少包含两款影像旗舰，实际: {models}"

    def test_camera_excludes_non_camera_phones(self, db_session):
        """测试拍照场景排除无影像标签的手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=10)
        models = [p.model for p in phones]

        # 无标签手机不应出现
        non_camera_models = ["Redmi Note 13", "iQOO 12", "红魔9 Pro"]
        for model in non_camera_models:
            assert model not in models, f"拍照场景不应返回无影像标签的手机: {model}"


class TestBatteryTagFilter:
    """测试续航场景标签筛选"""

    def test_battery_filters_by_tag_or_capacity(self, db_session):
        """测试续航场景筛选 features 包含'大电池'或'快充'的手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=10)

        # 断言1: 应该返回手机
        assert len(phones) > 0, "续航场景应返回手机"

        # 断言2: 所有返回的手机都应有续航标签或电池>=5000
        battery_features = ["大电池", "快充"]
        for phone in phones:
            has_battery_tag = (
                (phone.features and any(f in phone.features for f in battery_features)) or
                (phone.suitable_for and "续航" in phone.suitable_for) or
                (phone.battery and phone.battery >= 5000)
            )
            assert has_battery_tag, f"续航场景返回了无续航标签的手机: {phone.model}"

    def test_battery_includes_large_battery_phones(self, db_session):
        """测试续航场景应包含大电池手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=10)
        models = [p.model for p in phones]

        # 应包含大电池手机
        battery_models = ["vivo Y200", "荣耀Play9T", "红魔9 Pro"]
        found_count = sum(1 for m in battery_models if m in models)
        assert found_count >= 1, f"应至少包含一款大电池手机，实际: {models}"

    def test_battery_excludes_small_battery_phones(self, db_session):
        """测试续航场景排除小电池无标签手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=10)
        models = [p.model for p in phones]

        # 小电池手机不应出现 (除非有快充标签)
        # 小米14 电池 4610mAh < 5000，无大电池/快充标签，不应出现
        assert "小米14" not in models, "续航场景不应返回小电池无标签手机"


class TestCombinedTagFilters:
    """测试组合场景标签筛选"""

    def test_gaming_with_budget(self, db_session):
        """测试游戏场景+预算筛选"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"],
            budget_min=3000,
            budget_max=5000
        )

        phones = service.search(intent, limit=10)

        # 应返回价格在范围内的游戏手机
        for phone in phones:
            assert 3000 <= phone.price <= 5000, \
                f"预算筛选失败: {phone.model} 价格 {phone.price} 不在范围内"
            # 都应有游戏标签
            has_gaming_tag = (
                (phone.features and ("游戏" in phone.features or "电竞" in phone.features)) or
                (phone.suitable_for and "游戏玩家" in phone.suitable_for)
            )
            assert has_gaming_tag, f"应只返回游戏手机: {phone.model}"

    def test_camera_with_brand(self, db_session):
        """测试拍照场景+品牌筛选"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"],
            brands=["小米"]
        )

        phones = service.search(intent, limit=10)

        # 应只返回小米品牌
        for phone in phones:
            assert phone.brand == "小米", f"品牌筛选失败: 返回了 {phone.brand}"

        # 小米14 Ultra 应在结果中
        models = [p.model for p in phones]
        assert "小米14 Ultra" in models, f"应包含小米14 Ultra，实际: {models}"

    def test_no_features_returns_all(self, db_session):
        """测试无场景时返回所有手机（按价格排序）"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND
        )

        phones = service.search(intent, limit=10)

        # 应返回手机，无场景筛选
        assert len(phones) > 0, "无场景时应返回手机"


class TestBuildFeatureFiltersMethod:
    """直接测试 _build_feature_filters 方法"""

    def test_gaming_filter_conditions(self, db_session):
        """测试游戏场景生成正确的筛选条件"""
        service = RetrievalService(db_session)

        or_conditions, battery_threshold = service._build_feature_filters(["游戏"])

        # 应有筛选条件
        assert len(or_conditions) == 1, "游戏场景应生成1个筛选条件"
        # 电池阈值应为 None
        assert battery_threshold is None, "游戏场景不应设置电池阈值"

    def test_camera_filter_conditions(self, db_session):
        """测试拍照场景生成正确的筛选条件"""
        service = RetrievalService(db_session)

        or_conditions, battery_threshold = service._build_feature_filters(["拍照"])

        # 应有筛选条件
        assert len(or_conditions) == 1, "拍照场景应生成1个筛选条件"
        # 电池阈值应为 None
        assert battery_threshold is None, "拍照场景不应设置电池阈值"

    def test_battery_filter_conditions(self, db_session):
        """测试续航场景生成正确的筛选条件"""
        service = RetrievalService(db_session)

        or_conditions, battery_threshold = service._build_feature_filters(["续航"])

        # 应有筛选条件
        assert len(or_conditions) == 1, "续航场景应生成1个筛选条件"
        # 电池阈值应为 5000
        assert battery_threshold == 5000, "续航场景应设置电池阈值5000"

    def test_multiple_features_conditions(self, db_session):
        """测试多场景生成多个筛选条件"""
        service = RetrievalService(db_session)

        or_conditions, battery_threshold = service._build_feature_filters(["游戏", "拍照"])

        # 应有2个筛选条件（游戏+拍照）
        assert len(or_conditions) == 2, "游戏+拍照场景应生成2个筛选条件"

    def test_performance_no_filter(self, db_session):
        """测试性能场景不生成筛选条件"""
        service = RetrievalService(db_session)

        or_conditions, battery_threshold = service._build_feature_filters(["性能"])

        # 性能场景不添加DB筛选，依赖排序
        assert len(or_conditions) == 0, "性能场景不应生成筛选条件"
        assert battery_threshold is None, "性能场景不应设置电池阈值"

    def test_wireless_charging_filter(self, db_session):
        """测试无线充电筛选条件"""
        service = RetrievalService(db_session)

        or_conditions, battery_threshold = service._build_feature_filters(["无线充电"])

        # 应有筛选条件
        assert len(or_conditions) == 1, "无线充电场景应生成1个筛选条件"
        assert battery_threshold is None
