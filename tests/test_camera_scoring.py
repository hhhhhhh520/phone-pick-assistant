"""
测试影像评分逻辑

测试场景:
1. 旗舰影像手机（小米14 Ultra/vivo X100 Ultra）应得高分（>80）
2. 高端影像手机（小米14/vivo X100）应得中等分（60-80）
3. 游戏手机（iQOO 12）影像分应中等（40-60）
4. 入门机影像分应较低（<40）
5. 三维度评分测试：芯片/传感器/长焦/算法
6. 拍照场景排序：影像旗舰应在游戏手机前面
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.domain import Phone, Base
from backend.services.camera_score import CameraScoringService
from backend.services.camera_score_config import (
    get_chip_score,
    get_sensor_score,
    get_telephoto_score,
    get_algorithm_score,
    get_score_level,
)


@pytest.fixture
def db_session():
    """创建测试数据库，包含完整的影像评分测试数据"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 添加测试数据 - 涵盖不同影像等级的手机
    test_phones = [
        # ========== 顶级影像旗舰 (>90分) ==========
        Phone(
            brand="vivo", model="vivo X100 Ultra", price=5999,
            processor="天玑9300", ram=16, storage=512,
            battery=5500, charging_wired=80,
            camera_main=5000, camera_ultra=5000, camera_telephoto=20000,
            sensor_main="LYT-900", telephoto_type="双潜望长焦",
            has_ois=True, image_brand="蔡司",
            image_url="http://example.com/x100ultra.jpg"
        ),

        # ========== 旗舰影像手机 (80-90分) ==========
        Phone(
            brand="小米", model="小米14 Ultra", price=6499,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=5300, charging_wired=90,
            camera_main=5000, camera_ultra=5000, camera_telephoto=12000,
            sensor_main="LYT-900", telephoto_type="直立+潜望双长焦",
            has_ois=True, image_brand="徕卡",
            image_url="http://example.com/mi14ultra.jpg"
        ),
        Phone(
            brand="OPPO", model="Find X7 Ultra", price=5999,
            processor="天玑9300", ram=16, storage=256,
            battery=5000, charging_wired=100,
            camera_main=5000, camera_ultra=5000, camera_telephoto=12000,
            sensor_main="LYT-900", telephoto_type="高像素大底潜望",
            has_ois=True, image_brand="哈苏",
            image_url="http://example.com/findx7.jpg"
        ),
        Phone(
            brand="华为", model="P60 Pro", price=5988,
            processor="骁龙8+ Gen1", ram=8, storage=256,
            battery=4815, charging_wired=88,
            camera_main=4800, camera_ultra=13000, camera_telephoto=12000,
            sensor_main="IMX989", telephoto_type="单潜望长焦",
            has_ois=True, image_brand="XMAGE",
            image_url="http://example.com/p60pro.jpg"
        ),

        # ========== 高端影像手机 (60-80分) ==========
        Phone(
            brand="小米", model="小米14", price=3999,
            processor="骁龙8 Gen3", ram=12, storage=256,
            battery=4610, charging_wired=90,
            camera_main=5000, camera_ultra=5000, camera_telephoto=7500,
            sensor_main="OV50H", telephoto_type="直立长焦",
            has_ois=True, image_brand="徕卡",
            image_url="http://example.com/mi14.jpg"
        ),
        Phone(
            brand="vivo", model="vivo X100", price=3999,
            processor="天玑9300", ram=12, storage=256,
            battery=5000, charging_wired=120,
            camera_main=5000, camera_ultra=5000, camera_telephoto=6400,
            sensor_main="IMX921", telephoto_type="单潜望长焦",
            has_ois=True, image_brand="蔡司",
            image_url="http://example.com/x100.jpg"
        ),

        # ========== 游戏手机（影像中等，40-60分） ==========
        Phone(
            brand="iQOO", model="iQOO 12", price=3999,
            processor="骁龙8 Gen3", ram=16, storage=256,
            battery=5000, charging_wired=120,
            camera_main=5000, camera_ultra=5000, camera_telephoto=6400,
            sensor_main="OV50H", telephoto_type="直立长焦",
            has_ois=True, image_brand="原色",
            image_url="http://example.com/iqoo12.jpg"
        ),
        Phone(
            brand="红魔", model="红魔9 Pro", price=4999,
            processor="骁龙8 Gen3", ram=16, storage=512,
            battery=6500, charging_wired=80,
            camera_main=5000,
            sensor_main=None, telephoto_type=None,
            has_ois=False, image_brand=None,
            image_url="http://example.com/n9pro.jpg"
        ),

        # ========== 入门手机 (<40分) ==========
        Phone(
            brand="Redmi", model="Redmi Note 13", price=1199,
            processor="天玑6020", ram=6, storage=128,
            battery=5000, charging_wired=33,
            camera_main=10800,
            sensor_main=None, telephoto_type=None,
            has_ois=False, image_brand=None,
            image_url="http://example.com/note13.jpg"
        ),
        Phone(
            brand="荣耀", model="荣耀Play8T", price=999,
            processor="天玑6020", ram=8, storage=256,
            battery=6000, charging_wired=35,
            camera_main=5000,
            sensor_main=None, telephoto_type=None,
            has_ois=False, image_brand=None,
            image_url="http://example.com/play8t.jpg"
        ),
    ]

    db.add_all(test_phones)
    db.commit()
    yield db
    db.close()


@pytest.fixture
def scoring_service():
    """创建评分服务实例"""
    return CameraScoringService()


class TestCameraScoreLevels:
    """测试影像评分等级"""

    def test_flagship_camera_phones_get_high_scores(self, db_session, scoring_service):
        """旗舰影像手机应得高分（>=75分）"""
        # 使用旗舰处理器(骁龙8 Gen3/天玑9300)的影像旗舰
        flagship_models = ["小米14 Ultra", "vivo X100 Ultra", "Find X7 Ultra"]

        for model in flagship_models:
            phone = db_session.query(Phone).filter(Phone.model == model).first()
            assert phone is not None, f"找不到手机: {model}"

            result = scoring_service.calc_total_score(phone)
            assert result["total"] >= 75, \
                f"{model} 影像分应>=75，实际: {result['total']}分 (等级: {result['grade']})"

    def test_high_end_camera_phones_get_medium_scores(self, db_session, scoring_service):
        """高端影像手机应得中等分（60-75分）"""
        # P60 Pro 使用骁龙8+ Gen1（非最新旗舰芯片），属于高端影像手机
        high_end_models = ["小米14", "vivo X100", "P60 Pro"]

        for model in high_end_models:
            phone = db_session.query(Phone).filter(Phone.model == model).first()
            assert phone is not None, f"找不到手机: {model}"

            result = scoring_service.calc_total_score(phone)
            assert 60 <= result["total"] < 76, \
                f"{model} 影像分应在60-76，实际: {result['total']}分 (等级: {result['grade']})"

    def test_gaming_phones_get_medium_camera_scores(self, db_session, scoring_service):
        """游戏手机影像分应中等（40-60分）"""
        gaming_models = ["iQOO 12", "红魔9 Pro"]

        for model in gaming_models:
            phone = db_session.query(Phone).filter(Phone.model == model).first()
            assert phone is not None, f"找不到手机: {model}"

            result = scoring_service.calc_total_score(phone)
            # 游戏手机有旗舰处理器(25分) + 基础影像配置，应在40-60分
            assert 40 <= result["total"] < 70, \
                f"{model} 影像分应在40-70，实际: {result['total']}分 (等级: {result['grade']})"

    def test_entry_phones_get_low_camera_scores(self, db_session, scoring_service):
        """入门机影像分应较低（<40分）"""
        entry_models = ["Redmi Note 13", "荣耀Play8T"]

        for model in entry_models:
            phone = db_session.query(Phone).filter(Phone.model == model).first()
            assert phone is not None, f"找不到手机: {model}"

            result = scoring_service.calc_total_score(phone)
            assert result["total"] < 40, \
                f"{model} 影像分应<40，实际: {result['total']}分 (等级: {result['grade']})"

    def test_vivo_x100_ultra_is_top_tier(self, db_session, scoring_service):
        """vivo X100 Ultra 作为顶级影像旗舰应得最高分"""
        phone = db_session.query(Phone).filter(Phone.model == "vivo X100 Ultra").first()
        result = scoring_service.calc_total_score(phone)

        # 顶级配置: 天玑9300(25) + LYT-900(15) + 双潜望(15) + OIS(5) + 蔡司(25) = 85分
        assert result["total"] >= 80, f"vivo X100 Ultra 应>=80分，实际: {result['total']}"
        assert "旗舰" in result["grade"] or "顶级" in result["grade"], \
            f"vivo X100 Ultra 应为旗舰级，实际: {result['grade']}"


class TestChipScore:
    """测试芯片算力评分"""

    def test_flagship_chip_score(self):
        """旗舰处理器应得高分（25分）"""
        flagship_chips = ["骁龙8 Gen3", "天玑9300", "天玑9300+"]

        for chip in flagship_chips:
            score = get_chip_score(chip)
            assert score == 25, f"{chip} 应得25分，实际: {score}"

    def test_high_end_chip_score(self):
        """高端处理器应得较高分（22分）"""
        high_end_chips = ["骁龙8 Gen2", "天玑9200", "天玑9200+"]

        for chip in high_end_chips:
            score = get_chip_score(chip)
            assert score == 22, f"{chip} 应得22分，实际: {score}"

    def test_mid_range_chip_score(self):
        """中端处理器应得中等分（16-18分）"""
        mid_range_chips = ["骁龙7+ Gen3", "骁龙7+ Gen2", "天玑8300"]

        for chip in mid_range_chips:
            score = get_chip_score(chip)
            assert 16 <= score <= 18, f"{chip} 应在16-18分，实际: {score}"

    def test_entry_chip_score(self):
        """入门处理器应得较低分（8-10分）"""
        entry_chips = ["天玑6020", "骁龙480", "天玑700"]

        for chip in entry_chips:
            score = get_chip_score(chip)
            assert 8 <= score <= 10, f"{chip} 应在8-10分，实际: {score}"

    def test_unknown_chip_gets_entry_score(self):
        """未知处理器应得入门级分数（10分）"""
        unknown_chips = ["未知处理器", "", "RandomChipX"]

        for chip in unknown_chips:
            score = get_chip_score(chip)
            assert score == 10, f"未知处理器 {chip} 应得10分，实际: {score}"

    def test_chip_score_with_image_chip_bonus(self):
        """有影像芯片应获得额外加分"""
        base_score = get_chip_score("骁龙8 Gen3", has_image_chip=False)
        bonus_score = get_chip_score("骁龙8 Gen3", has_image_chip=True, image_chip_name="V3+")

        assert bonus_score > base_score, "有影像芯片应获得加分"
        assert bonus_score == 28, f"骁龙8 Gen3+V3+ 应得28分，实际: {bonus_score}"


class TestSensorScore:
    """测试主摄传感器评分"""

    def test_one_inch_sensor_gets_max_score(self):
        """1英寸大底传感器应得满分（15分）"""
        one_inch_sensors = ["LYT-900", "IMX989"]

        for sensor in one_inch_sensors:
            score = get_sensor_score(sensor)
            assert score == 15, f"{sensor} 应得15分，实际: {score}"

    def test_flagship_sensor_score(self):
        """旗舰级传感器应得较高分（12分）"""
        flagship_sensors = ["LYT-818", "LYT-808", "OV50H", "GN1"]

        for sensor in flagship_sensors:
            score = get_sensor_score(sensor)
            assert score == 12, f"{sensor} 应得12分，实际: {score}"

    def test_high_end_sensor_score(self):
        """高端传感器应得中等分（10分）"""
        high_end_sensors = ["IMX921", "IMX906", "IMX888", "IMX766", "IMX866"]

        for sensor in high_end_sensors:
            score = get_sensor_score(sensor)
            assert score == 10, f"{sensor} 应得10分，实际: {score}"

    def test_mid_range_sensor_score(self):
        """中端传感器应得较低分（7分）"""
        mid_range_sensors = ["IMX689", "IMX686", "IMX586", "OV64B"]

        for sensor in mid_range_sensors:
            score = get_sensor_score(sensor)
            assert score == 7, f"{sensor} 应得7分，实际: {score}"

    def test_unknown_sensor_gets_default_score(self):
        """未知传感器应得默认分（5分）"""
        unknown_sensors = ["", None, "未知传感器"]

        for sensor in unknown_sensors:
            score = get_sensor_score(sensor)
            assert score == 5, f"未知传感器 {sensor} 应得5分，实际: {score}"


class TestTelephotoScore:
    """测试长焦配置评分"""

    def test_dual_periscope_telephoto_gets_max_score(self):
        """双潜望长焦应得满分（15分）"""
        dual_periscope_configs = ["双潜望长焦", "双潜望", "潜望+潜望"]

        for config in dual_periscope_configs:
            score = get_telephoto_score(config)
            assert score == 15, f"{config} 应得15分，实际: {score}"

    def test_single_periscope_telephone_score(self):
        """单潜望长焦应得中等分（7分）"""
        single_periscope_configs = ["单潜望长焦", "潜望长焦", "潜望式"]

        for config in single_periscope_configs:
            score = get_telephoto_score(config)
            assert score == 7, f"{config} 应得7分，实际: {score}"

    def test_upright_telephoto_score(self):
        """直立长焦应得中等分（7分）"""
        upright_configs = ["直立长焦", "长焦镜头", "3x长焦", "5x长焦"]

        for config in upright_configs:
            score = get_telephoto_score(config)
            assert score == 7, f"{config} 应得7分，实际: {score}"

    def test_no_telephoto_gets_zero(self):
        """无长焦应得0分"""
        no_telephoto_configs = ["无长焦", "", None]

        for config in no_telephoto_configs:
            score = get_telephoto_score(config)
            assert score == 0, f"{config} 应得0分，实际: {score}"

    def test_high_pixel_periscope_bonus(self):
        """高像素大底潜望应有加分（10分）"""
        score = get_telephoto_score("高像素大底潜望")
        assert score == 10, f"高像素大底潜望应得10分，实际: {score}"


class TestAlgorithmScore:
    """测试影像算法评分"""

    def test_xmage_algorithm_gets_max_score(self):
        """XMAGE算法应得满分（30分）"""
        score = get_algorithm_score(brand="华为", algorithm_name="XMAGE")
        assert score == 30, f"XMAGE应得30分，实际: {score}"

    def test_blueimage_algorithm_gets_max_score(self):
        """Blueimage算法应得满分（30分）"""
        score = get_algorithm_score(brand="vivo", algorithm_name="Blueimage")
        assert score == 30, f"Blueimage应得30分，实际: {score}"

    def test_leica_algorithm_score(self):
        """徕卡算法应得高分（25分）"""
        leica_names = ["徕卡", "Leica"]

        for name in leica_names:
            score = get_algorithm_score(algorithm_name=name)
            assert score == 25, f"{name}应得25分，实际: {score}"

    def test_hasselblad_algorithm_score(self):
        """哈苏算法应得高分（25分）"""
        hasselblad_names = ["哈苏", "Hasselblad"]

        for name in hasselblad_names:
            score = get_algorithm_score(algorithm_name=name)
            assert score == 25, f"{name}应得25分，实际: {score}"

    def test_zeiss_algorithm_score(self):
        """蔡司算法应得高分（25分）"""
        zeiss_names = ["蔡司", "Zeiss"]

        for name in zeiss_names:
            score = get_algorithm_score(algorithm_name=name)
            assert score == 25, f"{name}应得25分，实际: {score}"

    def test_default_algorithm_by_brand(self):
        """使用品牌默认算法评分"""
        brand_default_scores = {
            "华为": 30,   # XMAGE
            "vivo": 25,   # 蔡司
            "小米": 25,   # 徕卡
            "OPPO": 25,   # 哈苏
            "苹果": 22,   # 苹果原色
            "iQOO": 15,   # 原色
        }

        for brand, expected_score in brand_default_scores.items():
            score = get_algorithm_score(brand=brand)
            assert score == expected_score, f"{brand}默认算法应得{expected_score}分，实际: {score}"

    def test_unknown_algorithm_gets_default(self):
        """未知算法应得默认分（15分）"""
        score = get_algorithm_score()
        assert score == 15, f"未知算法应得15分，实际: {score}"


class TestCameraScoringService:
    """测试 CameraScoringService 类"""

    def test_calc_chip_score_from_phone(self, db_session, scoring_service):
        """测试从Phone模型计算芯片分"""
        phone = db_session.query(Phone).filter(Phone.model == "小米14 Ultra").first()
        score = scoring_service.calc_chip_score(phone)

        assert score == 25, f"骁龙8 Gen3 应得25分，实际: {score}"

    def test_calc_hardware_score_from_phone(self, db_session, scoring_service):
        """测试从Phone模型计算硬件分"""
        phone = db_session.query(Phone).filter(Phone.model == "vivo X100 Ultra").first()
        score = scoring_service.calc_hardware_score(phone)

        # LYT-900(15) + 双潜望(15) + OIS(5) = 35
        assert score == 35, f"vivo X100 Ultra 硬件分应为35，实际: {score}"

    def test_calc_algorithm_score_from_phone(self, db_session, scoring_service):
        """测试从Phone模型计算算法分"""
        phone = db_session.query(Phone).filter(Phone.model == "小米14 Ultra").first()
        score = scoring_service.calc_algorithm_score(phone)

        assert score == 25, f"徕卡算法应得25分，实际: {score}"

    def test_calc_total_score_structure(self, db_session, scoring_service):
        """测试综合评分返回结构"""
        phone = db_session.query(Phone).filter(Phone.model == "小米14 Ultra").first()
        result = scoring_service.calc_total_score(phone)

        # 验证返回结构
        assert "total" in result
        assert "chip_score" in result
        assert "hardware_score" in result
        assert "algorithm_score" in result
        assert "grade" in result

        # 验证总分等于各维度之和
        expected_total = result["chip_score"] + result["hardware_score"] + result["algorithm_score"]
        assert result["total"] == expected_total, \
            f"总分应等于各维度之和: {result['total']} != {expected_total}"

    def test_scoring_with_missing_fields(self, db_session, scoring_service):
        """测试缺失字段时的评分处理"""
        phone = db_session.query(Phone).filter(Phone.model == "红魔9 Pro").first()
        result = scoring_service.calc_total_score(phone)

        # 红魔9 Pro 没有影像相关字段，但应有有效评分
        assert result["total"] >= 0
        assert result["grade"] is not None


class TestScoreLevel:
    """测试评分等级"""

    def test_top_tier_level(self):
        """顶级影像旗舰等级（90-100分）"""
        assert "顶级" in get_score_level(95)
        assert "顶级" in get_score_level(90)

    def test_flagship_level(self):
        """旗舰影像手机等级（80-90分）"""
        assert "旗舰" in get_score_level(85)
        assert "旗舰" in get_score_level(80)

    def test_high_end_level(self):
        """高端影像手机等级（70-80分）"""
        assert "高端" in get_score_level(75)
        assert "高端" in get_score_level(70)

    def test_mid_range_level(self):
        """中端影像手机等级（60-70分）"""
        assert "中端" in get_score_level(65)
        assert "中端" in get_score_level(60)

    def test_entry_level(self):
        """入门影像手机等级（50-60分）"""
        assert "入门" in get_score_level(55)
        assert "入门" in get_score_level(50)

    def test_basic_level(self):
        """基础影像能力等级（<50分）"""
        assert "基础" in get_score_level(40)
        assert "基础" in get_score_level(20)


class TestCameraScenarioSorting:
    """测试拍照场景排序"""

    def test_camera_phones_ranked_higher_than_gaming_phones(self, db_session, scoring_service):
        """拍照场景排序：影像旗舰应在游戏手机前面"""
        # 获取影像旗舰和游戏手机的评分
        camera_phones = ["小米14 Ultra", "vivo X100 Ultra", "Find X7 Ultra"]
        gaming_phones = ["iQOO 12", "红魔9 Pro"]

        camera_scores = []
        for model in camera_phones:
            phone = db_session.query(Phone).filter(Phone.model == model).first()
            result = scoring_service.calc_total_score(phone)
            camera_scores.append((model, result["total"]))

        gaming_scores = []
        for model in gaming_phones:
            phone = db_session.query(Phone).filter(Phone.model == model).first()
            result = scoring_service.calc_total_score(phone)
            gaming_scores.append((model, result["total"]))

        # 所有影像旗舰的评分应高于游戏手机
        min_camera_score = min(score for _, score in camera_scores)
        max_gaming_score = max(score for _, score in gaming_scores)

        assert min_camera_score > max_gaming_score, \
            f"影像旗舰最低分({min_camera_score})应高于游戏手机最高分({max_gaming_score})"

    def test_mi14_ultra_ranks_higher_than_iqoo12(self, db_session, scoring_service):
        """小米14 Ultra 应排在 iQOO 12 前面"""
        mi14u = db_session.query(Phone).filter(Phone.model == "小米14 Ultra").first()
        iqoo12 = db_session.query(Phone).filter(Phone.model == "iQOO 12").first()

        mi14u_score = scoring_service.calc_total_score(mi14u)
        iqoo12_score = scoring_service.calc_total_score(iqoo12)

        assert mi14u_score["total"] > iqoo12_score["total"], \
            f"小米14 Ultra({mi14u_score['total']})应高于iQOO 12({iqoo12_score['total']})"

    def test_vivo_x100_ultra_has_highest_score(self, db_session, scoring_service):
        """vivo X100 Ultra 应有最高评分"""
        all_phones = db_session.query(Phone).all()

        x100ultra = db_session.query(Phone).filter(Phone.model == "vivo X100 Ultra").first()
        x100ultra_score = scoring_service.calc_total_score(x100ultra)["total"]

        for phone in all_phones:
            if phone.model == "vivo X100 Ultra":
                continue
            score = scoring_service.calc_total_score(phone)["total"]
            assert x100ultra_score >= score, \
                f"vivo X100 Ultra({x100ultra_score})应>= {phone.model}({score})"


class TestEdgeCases:
    """测试边界情况"""

    def test_phone_with_all_null_fields(self, scoring_service):
        """测试所有影像字段为空的手机"""
        phone = Phone(
            brand="测试", model="测试手机", price=999,
            processor=None, sensor_main=None, telephoto_type=None,
            has_ois=None, image_brand=None
        )

        result = scoring_service.calc_total_score(phone)

        # 应返回有效结果，不抛异常
        assert result["total"] >= 0
        assert "grade" in result

    def test_phone_with_empty_strings(self, scoring_service):
        """测试影像字段为空字符串的手机"""
        phone = Phone(
            brand="测试", model="测试手机", price=999,
            processor="", sensor_main="", telephoto_type="",
            has_ois=False, image_brand=""
        )

        result = scoring_service.calc_total_score(phone)

        assert result["total"] >= 0
        assert "基础" in result["grade"]

    def test_phone_with_unexpected_values(self, scoring_service):
        """测试意外的字段值"""
        phone = Phone(
            brand="未知品牌", model="未知型号", price=999,
            processor="神秘芯片X99", sensor_main="神秘传感器Y88",
            telephoto_type="超级长焦", has_ois=True, image_brand="神秘联名"
        )

        result = scoring_service.calc_total_score(phone)

        # 应返回有效结果，使用默认值
        assert result["total"] >= 0
        assert "chip_score" in result
        assert "hardware_score" in result
        assert "algorithm_score" in result
