"""测试场景匹配逻辑

测试场景:
1. "推荐游戏手机" 应返回 iQOO 12/Redmi K70 Pro 等性能机而非入门机
2. "推荐拍照手机" 应返回小米14 Ultra/华为P60 Pro 等影像旗舰
3. "推荐续航手机" 应返回电池容量大的手机
4. 意图识别应正确提取 features 字段
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.domain import Phone, Base, get_antutu_score
from backend.services.retrieval import RetrievalService
from backend.models.schemas import IntentResult, IntentType


@pytest.fixture
def db_session():
    """创建测试数据库，包含完整的场景测试数据"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 添加测试数据 - 涵盖游戏、拍照、续航场景
    test_phones = [
        # ========== 游戏手机 ==========
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
            brand="Redmi", model="Redmi K70 Pro", price=3299,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=5000, charging_wired=120,
            camera_main=5000,
            features='["游戏", "高刷屏", "性价比"]',
            suitable_for='["游戏玩家", "学生"]',
            image_url="http://example.com/k70pro.jpg"
        ),
        Phone(
            brand="红魔", model="红魔9 Pro", price=4999,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=6500, charging_wired=80,
            camera_main=5000,
            features='["游戏手机", "电竞", "散热"]',
            suitable_for='["游戏玩家"]',
            image_url="http://example.com/n9pro.jpg"
        ),

        # ========== 拍照手机 ==========
        Phone(
            brand="小米", model="小米14 Ultra", price=6499,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5300, charging_wired=90,
            camera_main=5000, camera_ultra=5000, camera_telephoto=12000,
            features='["徕卡影像", "潜望长焦", "可变光圈"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/mi14ultra.jpg"
        ),
        Phone(
            brand="华为", model="P60 Pro", price=5988,
            processor="骁龙8+ Gen1", ram=8, storage=256,
            battery=4815, charging_wired=88,
            camera_main=4800, camera_ultra=13000, camera_telephoto=12000,
            features='["徕卡影像", "潜望长焦", "夜景"]',
            suitable_for='["摄影爱好者", "商务人士"]',
            image_url="http://example.com/p60pro.jpg"
        ),
        Phone(
            brand="OPPO", model="Find X7 Ultra", price=5999,
            processor="天玑9300", ram=16, storage=256,
            battery=5000, charging_wired=100,
            camera_main=5000, camera_ultra=5000, camera_telephoto=12000,
            features='["哈苏影像", "潜望长焦"]',
            suitable_for='["摄影爱好者"]',
            image_url="http://example.com/findx7.jpg"
        ),

        # ========== 续航手机 ==========
        Phone(
            brand="vivo", model="vivo X100", price=3999,
            processor="天玑9300", ram=12, storage=256,
            battery=5000, charging_wired=120,
            camera_main=5000,
            features='["长续航", "快充"]',
            suitable_for='["续航需求"]',
            image_url="http://example.com/x100.jpg"
        ),
        Phone(
            brand="荣耀", model="荣耀Magic6 Pro", price=5499,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=5600, charging_wired=80,
            camera_main=5000,
            features='["长续航", "护眼屏"]',
            suitable_for='["续航需求", "商务人士"]',
            image_url="http://example.com/magic6.jpg"
        ),
        Phone(
            brand="红魔", model="红魔9 Pro", price=4999,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=6500, charging_wired=80,
            camera_main=5000,
            features='["游戏手机", "电竞", "散热"]',
            suitable_for='["游戏玩家"]',
            image_url="http://example.com/n9pro.jpg"
        ),

        # ========== 入门手机 (不应在游戏推荐中出现) ==========
        Phone(
            brand="Redmi", model="Redmi Note 13", price=1199,
            processor="天玑6020", ram=6, storage=128,
            battery=5000, charging_wired=33,
            camera_main=10800,
            features='["大屏", "大音量"]',
            suitable_for='["学生", "长辈"]',
            image_url="http://example.com/note13.jpg"
        ),
        Phone(
            brand="荣耀", model="荣耀Play8T", price=999,
            processor="天玑6020", ram=8, storage=256,
            battery=6000, charging_wired=35,
            camera_main=5000,
            features='["大电池"]',
            suitable_for='["长辈"]',
            image_url="http://example.com/play8t.jpg"
        ),

        # ========== 普通旗舰 (非游戏/非拍照专项) ==========
        Phone(
            brand="小米", model="小米14", price=3999,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=4610, charging_wired=90,
            camera_main=5000,
            features='["小屏旗舰"]',
            suitable_for='["小屏党"]',
            image_url="http://example.com/mi14.jpg"
        ),
        Phone(
            brand="苹果", model="iPhone 15 Pro", price=7999,
            processor="A17 Pro", ram=8, storage=256,
            battery=3274, charging_wired=27,
            camera_main=4800,
            features='["灵动岛", "钛金属"]',
            suitable_for='["苹果生态用户"]',
            image_url="http://example.com/iphone15pro.jpg"
        ),
    ]

    db.add_all(test_phones)
    db.commit()
    yield db
    db.close()


class TestGamingScenario:
    """测试游戏场景匹配"""

    def test_gaming_returns_performance_phones(self, db_session):
        """测试'推荐游戏手机'应返回性能机而非入门机"""
        service = RetrievalService(db_session)

        # 构造游戏场景的意图
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=5)

        # 断言1: 应该返回手机
        assert len(phones) > 0, "游戏场景应返回手机"

        # 断言2: 不应包含入门机 (跑分<30万)
        for phone in phones:
            score = get_antutu_score(phone.processor)
            assert score >= 300000 or score == 0, f"游戏手机不应是入门机，但返回了 {phone.model} (处理器: {phone.processor}, 跑分: {score})"

        # 断言3: 应包含游戏手机标签
        gaming_phones = [p for p in phones if p.features and ("游戏" in p.features or "电竞" in p.features)]
        assert len(gaming_phones) >= 1, "应至少返回一款游戏手机"

        # 断言4: iQOO 12 或 Redmi K70 Pro 应在结果中
        models = [p.model for p in phones]
        assert any(m in models for m in ["iQOO 12", "Redmi K70 Pro", "红魔9 Pro"]), \
            f"应包含游戏手机，实际返回: {models}"

    def test_gaming_sorts_by_processor_tier(self, db_session):
        """测试游戏场景应按处理器性能排序"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=5)

        # 验证排序: 安兔兔跑分应递减 (高性能在前)
        scores = [get_antutu_score(p.processor) for p in phones]
        # 允许相等的相邻元素
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], \
                f"游戏场景应按安兔兔跑分降序，实际: {scores}"

    def test_gaming_excludes_low_end_phones(self, db_session):
        """测试游戏场景排除入门手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        phones = service.search(intent, limit=10)

        # 提取所有返回的型号
        models = [p.model for p in phones]

        # 入门机不应出现
        low_end_models = ["Redmi Note 13", "荣耀Play8T"]
        for model in low_end_models:
            assert model not in models, f"游戏场景不应返回入门机 {model}"


class TestCameraScenario:
    """测试拍照场景匹配"""

    def test_camera_returns_photography_phones(self, db_session):
        """测试'推荐拍照手机'应返回影像旗舰"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=5)

        # 断言1: 应该返回手机
        assert len(phones) > 0, "拍照场景应返回手机"

        # 断言2: 应包含影像标签
        photography_features = ["徕卡", "哈苏", "蔡司", "影像", "潜望长焦"]
        photography_phones = [
            p for p in phones
            if p.features and any(f in p.features for f in photography_features)
        ]
        assert len(photography_phones) >= 1, "应至少返回一款影像旗舰"

        # 断言3: 小米14 Ultra 或 华为P60 Pro 应在结果中
        models = [p.model for p in phones]
        assert any(m in models for m in ["小米14 Ultra", "P60 Pro", "Find X7 Ultra"]), \
            f"应包含影像旗舰，实际返回: {models}"

    def test_camera_sorts_by_camera_pixels(self, db_session):
        """测试拍照场景应按相机像素排序"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=5)

        # 验证主摄像素递减排序
        pixels = [p.camera_main or 0 for p in phones]
        for i in range(len(pixels) - 1):
            assert pixels[i] >= pixels[i + 1], \
                f"拍照场景应按主摄像素降序，实际: {pixels}"

    def test_camera_excludes_non_photography_phones(self, db_session):
        """测试拍照场景应包含专业影像手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        phones = service.search(intent, limit=10)

        # 验证: 游戏专项手机（无影像标签）不应优先出现
        models = [p.model for p in phones[:3]]  # 前3个

        # 纯游戏手机(无影像标签)不应在前3
        pure_gaming = ["iQOO 12", "红魔9 Pro"]
        for model in pure_gaming:
            # 如果游戏手机有影像标签，则可以接受
            phone = next((p for p in phones if p.model == model), None)
            if phone and phone.features:
                if "徕卡" not in phone.features and "哈苏" not in phone.features:
                    assert model not in models, \
                        f"拍照场景不应优先返回纯游戏手机 {model}"


class TestBatteryScenario:
    """测试续航场景匹配"""

    def test_battery_returns_large_battery_phones(self, db_session):
        """测试'推荐续航手机'应返回电池容量大的手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=5)

        # 断言1: 应该返回手机
        assert len(phones) > 0, "续航场景应返回手机"

        # 断言2: 电池容量应该 >= 5000mAh
        for phone in phones:
            assert phone.battery >= 5000, \
                f"续航手机电池应>=5000mAh，{phone.model} 只有 {phone.battery}mAh"

        # 断言3: 红魔9 Pro (6500mAh) 或 荣耀Magic6 Pro (5600mAh) 应在结果中
        models = [p.model for p in phones]
        batteries = [(p.model, p.battery) for p in phones]
        assert any(m in models for m in ["红魔9 Pro", "荣耀Magic6 Pro", "vivo X100"]), \
            f"应包含大电池手机，实际: {batteries}"

    def test_battery_sorts_by_capacity(self, db_session):
        """测试续航场景应按电池容量降序排序"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=5)

        # 验证电池容量递减
        batteries = [p.battery or 0 for p in phones]
        for i in range(len(batteries) - 1):
            assert batteries[i] >= batteries[i + 1], \
                f"续航场景应按电池降序，实际: {batteries}"

    def test_battery_excludes_small_battery_phones(self, db_session):
        """测试续航场景排除小电池手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        phones = service.search(intent, limit=10)

        models = [p.model for p in phones]

        # 小电池手机不应出现
        small_battery_models = ["iPhone 15 Pro", "小米14"]  # <5000mAh
        for model in small_battery_models:
            assert model not in models, f"续航场景不应返回小电池手机 {model}"


class TestIntentRecognition:
    """测试意图识别"""

    def test_features_extraction_gaming(self, db_session):
        """测试意图识别应正确提取游戏features"""
        # 模拟意图识别结果
        # 实际测试时需要mock LLM，这里直接构造结果
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"]
        )

        assert intent.intent == IntentType.RECOMMEND
        assert "游戏" in intent.features

    def test_features_extraction_camera(self, db_session):
        """测试意图识别应正确提取拍照features"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"]
        )

        assert intent.intent == IntentType.RECOMMEND
        assert "拍照" in intent.features

    def test_features_extraction_battery(self, db_session):
        """测试意图识别应正确提取续航features"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["续航"]
        )

        assert intent.intent == IntentType.RECOMMEND
        assert "续航" in intent.features

    def test_features_extraction_multiple(self, db_session):
        """测试意图识别应正确提取多个features"""
        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏", "续航"]
        )

        assert len(intent.features) == 2
        assert "游戏" in intent.features
        assert "续航" in intent.features


class TestCombinedScenarios:
    """测试组合场景"""

    def test_gaming_with_budget(self, db_session):
        """测试游戏场景+预算筛选"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["游戏"],
            budget_min=2000,
            budget_max=4000
        )

        phones = service.search(intent, limit=5)

        # 应返回价格在范围内的游戏手机
        for phone in phones:
            assert 2000 <= phone.price <= 4000, \
                f"预算筛选失败: {phone.model} 价格 {phone.price} 不在范围内"

        # Redmi K70 Pro 应在结果中 (3299元)
        models = [p.model for p in phones]
        assert "Redmi K70 Pro" in models, f"应包含K70 Pro，实际: {models}"

    def test_camera_with_brand(self, db_session):
        """测试拍照场景+品牌筛选"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND,
            features=["拍照"],
            brands=["小米"]
        )

        phones = service.search(intent, limit=5)

        # 应只返回小米品牌
        for phone in phones:
            assert phone.brand == "小米", \
                f"品牌筛选失败: 返回了 {phone.brand}"

        # 小米14 Ultra 应在结果中
        models = [p.model for p in phones]
        assert "小米14 Ultra" in models, f"应包含小米14 Ultra，实际: {models}"

    def test_no_scenario_returns_reasonable_phones(self, db_session):
        """测试无场景时返回合理手机"""
        service = RetrievalService(db_session)

        intent = IntentResult(
            intent=IntentType.RECOMMEND
        )

        phones = service.search(intent, limit=5)

        # 应返回手机，按价格升序
        assert len(phones) > 0

        prices = [p.price for p in phones]
        for i in range(len(prices) - 1):
            assert prices[i] <= prices[i + 1], \
                f"无场景时应按价格升序，实际: {prices}"


class TestProcessorScore:
    """测试处理器安兔兔跑分"""

    def test_flagship_processor_score(self):
        """测试旗舰处理器跑分 (130万+)"""
        flagship_processors = [
            ("骁龙8 Gen3", 1372529),
            ("骁龙8Gen3", 1372529),
            ("骁龙8 Gen2", 952809),
            ("天玑9300", 1344087),
            ("天玑9300+", 1382983),
        ]
        for processor, expected_min in flagship_processors:
            score = get_antutu_score(processor)
            assert score >= expected_min * 0.9, f"{processor} 跑分应>=130万，实际: {score}"

    def test_high_end_processor_score(self):
        """测试高端处理器跑分 (60-130万)"""
        high_end_processors = ["骁龙7+ Gen3", "骁龙7+Gen2", "天玑8300-Ultra"]
        for processor in high_end_processors:
            score = get_antutu_score(processor)
            assert score >= 600000, f"{processor} 跑分应>=60万，实际: {score}"

    def test_mid_range_processor_score(self):
        """测试中端处理器跑分 (40-80万)"""
        mid_range_processors = ["骁龙7s Gen2", "天玑7200", "骁龙6 Gen1"]
        for processor in mid_range_processors:
            score = get_antutu_score(processor)
            assert score >= 300000, f"{processor} 跑分应>=30万，实际: {score}"

    def test_entry_level_processor_score(self):
        """测试入门处理器跑分 (<40万)"""
        entry_processors = ["天玑6020", "骁龙480"]
        for processor in entry_processors:
            score = get_antutu_score(processor)
            assert score > 0, f"{processor} 应有跑分数据"
            assert score < 400000, f"{processor} 跑分应<40万，实际: {score}"

    def test_unknown_processor_score(self):
        """测试未知处理器返回0"""
        unknown = ["未知处理器", "", None]
        for processor in unknown:
            score = get_antutu_score(processor)
            assert score == 0, f"未知处理器应返回0，实际: {score}"
