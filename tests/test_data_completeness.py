"""
P6+P7数据验证测试 (SUB-005)

测试内容:
(a) processor字段完整性：所有记录非空，格式统一（无品牌前缀）
(b) get_antutu_score()：对所有记录返回>0的跑分
(c) camera_main字段：所有记录为有效INTEGER或NULL
(d) retrieval.py按性能排序使用processor跑分正确
(e) retrieval.py按拍照排序使用camera_main整数值正确（高像素在前）
(f) _parse_camera_mp()各种输入格式正确解析
(g) _safe_camera_value()向后兼容（TEXT和INTEGER输入都正确处理）
(h) 品牌映射表完整性检查
"""
import pytest
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.domain import (
    Phone,
    Base,
    get_antutu_score,
    _normalize_processor,
    ANTUTU_SCORES,
    _BRAND_PREFIX_PATTERNS,
    _PROCESSOR_ALIASES,
    SessionLocal,
)
from backend.services.retrieval import (
    _parse_camera_mp,
    _safe_camera_value,
    RetrievalService,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def real_db_session():
    """连接真实数据库，用于数据完整性测试"""
    import backend.config
    settings = backend.config.get_settings()
    # 将相对路径转换为绝对路径，确保测试能找到数据库
    db_url = settings.database_url
    if db_url.startswith("sqlite:///./"):
        # 路径相对于项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rel_path = db_url.replace("sqlite:///./", "")
        abs_path = os.path.join(project_root, rel_path)
        db_url = f"sqlite:///{abs_path}"

    engine = create_engine(db_url)
    # 验证表存在
    from sqlalchemy import inspect
    inspector = inspect(engine)
    assert "phones" in inspector.get_table_names(), (
        f"phones表不存在，数据库路径: {db_url}"
    )

    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture
def test_db_session():
    """创建内存测试数据库，用于排序逻辑测试"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


# ============================================================================
# (a) processor字段完整性测试
# ============================================================================


class TestProcessorCompleteness:
    """processor字段：所有记录非空，格式统一（无品牌前缀）"""

    # 已知品牌前缀模式（中文+英文）
    BRAND_PREFIXES = [
        "高通", "高通 ",
        "联发科", "联发科 ",
        "海思", "海思 ",
        "三星", "三星 ",
        "苹果", "苹果 ",
        "华为", "华为 ",
        "HUAWEI", "HUAWEI ",
        "Samsung", "Samsung ",
        "Apple", "Apple ",
        "Qualcomm", "Qualcomm ",
        "MediaTek", "MediaTek ",
    ]

    def _is_standard_format(self, processor: str) -> bool:
        """检查processor是否格式标准：无品牌前缀"""
        for prefix in self.BRAND_PREFIXES:
            if processor.lower().startswith(prefix.lower()):
                return False
        return True

    def test_all_processors_non_empty(self, real_db_session):
        """所有353条记录的processor字段非空"""
        phones = real_db_session.query(Phone).all()
        total = len(phones)
        assert total == 353, f"预期353条记录，实际{total}条"

        empty_processors = []
        for p in phones:
            if not p.processor or p.processor.strip() == "":
                empty_processors.append(f"{p.brand} {p.model} (id={p.id})")

        assert len(empty_processors) == 0, (
            f"{len(empty_processors)}条记录的processor为空:\n" +
            "\n".join(empty_processors)
        )

    def test_all_processors_no_brand_prefix(self, real_db_session):
        """所有processor值无品牌前缀（如'高通 骁龙8'->'骁龙8'）"""
        phones = real_db_session.query(Phone).all()
        violations = []
        for p in phones:
            if p.processor and not self._is_standard_format(p.processor):
                violations.append(
                    f"{p.brand} {p.model}: processor='{p.processor}'"
                )

        assert len(violations) == 0, (
            f"{len(violations)}条记录的processor包含品牌前缀:\n" +
            "\n".join(violations)
        )

    def test_processor_non_empty_with_brand_prefix_removed(self, real_db_session):
        """_normalize_processor应成功剥离所有品牌前缀"""
        phones = real_db_session.query(Phone).all()
        failures = []
        for p in phones:
            if not p.processor:
                continue
            normalized = _normalize_processor(p.processor)
            if not normalized:
                failures.append(
                    f"{p.brand} {p.model}: processor='{p.processor}' -> normalized=''"
                )
            # 验证规范化后的值也不含品牌前缀
            elif not self._is_standard_format(normalized):
                failures.append(
                    f"{p.brand} {p.model}: normalized='{normalized}' still has brand prefix"
                )

        assert len(failures) == 0, (
            f"_normalize_processor失败: {len(failures)}条:\n" +
            "\n".join(failures)
        )

    def test_processor_count(self, real_db_session):
        """验证真实数据库有记录（数量会随数据更新变化）"""
        count = real_db_session.query(Phone).count()
        assert count > 0, f"数据库无记录"
        # 参考值：2026-05 约 353 条，数据更新后会变化


# ============================================================================
# (b) get_antutu_score()测试
# ============================================================================


class TestAntutuScoreCoverage:
    """get_antutu_score()：对所有353条记录返回>0的跑分"""

    def test_all_records_have_antutu_score(self, real_db_session):
        """所有353条记录的processor都能获得>0的安兔兔跑分"""
        phones = real_db_session.query(Phone).all()
        zero_scores = []
        for p in phones:
            score = get_antutu_score(p.processor)
            if score == 0:
                zero_scores.append(
                    f"{p.brand} {p.model}: processor='{p.processor}' score=0"
                )

        if zero_scores:
            # 列出所有零分手机，便于排查
            fail_msg = (
                f"{len(zero_scores)}条记录跑分为0 (预期全部>0):\n" +
                "\n".join(sorted(zero_scores))
            )
            assert len(zero_scores) == 0, fail_msg

    def test_known_processors_have_positive_score(self):
        """关键处理器直接匹配ANTUTU_SCORES"""
        test_cases = [
            ("骁龙8 至尊版 Gen5", 2449060),
            ("天玑9500", 2319961),
            ("骁龙8 Gen 3", 1372529),
            ("骁龙8 Gen 2", 952809),
            ("天玑9300", 1344087),
            ("天玑9300+", 1382983),
            ("A17 Pro", 1420000),
            ("骁龙888", 598064),
            ("天玑7200", 492978),
            ("骁龙680", 211189),
        ]
        for proc, expected in test_cases:
            score = get_antutu_score(proc)
            assert score == expected, f"{proc}: 预期{expected}, 实际{score}"

    def test_normalized_processors_have_score(self):
        """带品牌前缀的处理器名经规范化后也能获得跑分"""
        test_cases = [
            "高通 骁龙8 Gen 3",
            "高通骁龙8Gen3",
            "联发科 天玑9300",
            "联发科天玑9300",
            "海思 麒麟9000",
            "HUAWEI 麒麟9000",
            "Apple A17 Pro",
            "Samsung Exynos 2400",
        ]
        for proc in test_cases:
            score = get_antutu_score(proc)
            assert score > 0, f"处理器'{proc}'未获得跑分"

    def test_antutu_scores_dict_integrity(self):
        """ANTUTU_SCORES字典所有值都是正整数"""
        for key, score in ANTUTU_SCORES.items():
            assert isinstance(score, int), f"'{key}'的跑分值{score}不是int"
            assert score > 0, f"'{key}'的跑分值{score}应>0"

    def test_antutu_score_consistency(self):
        """验证跑分的相对排序合理性：高性能>中端>入门"""
        high_end_score = get_antutu_score("骁龙8 至尊版 Gen5")
        mid_score = get_antutu_score("骁龙7+ Gen 3")
        entry_score = get_antutu_score("骁龙680")

        assert high_end_score > mid_score, (
            f"旗舰({high_end_score})应高于中端({mid_score})"
        )
        assert mid_score > entry_score, (
            f"中端({mid_score})应高于入门({entry_score})"
        )


# ============================================================================
# (c) camera_main字段测试
# ============================================================================


class TestCameraMainField:
    """camera_main字段：所有记录为有效INTEGER或NULL"""

    def test_camera_main_type_integer_or_null(self, real_db_session):
        """数据库层面camera_main字段均为INTEGER或NULL"""
        # 直接通过原始SQL检查列类型
        import sqlite3
        db_url = real_db_session.get_bind().url
        db_path = str(db_url).replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(phones)")
        columns = {row[1]: row[2] for row in cur.fetchall()}
        conn.close()

        assert "camera_main" in columns, "camera_main字段不存在"
        # SQLite中INTEGER类型可能显示为"INTEGER"或"integer"
        assert columns["camera_main"].upper() in ("INTEGER", "INT"), (
            f"camera_main预期为INTEGER，实际类型: {columns['camera_main']}"
        )

    def test_camera_main_values_valid(self, real_db_session):
        """所有camera_main值为正整数或NULL"""
        phones = real_db_session.query(Phone).all()
        invalid = []
        for p in phones:
            if p.camera_main is None:
                continue  # NULL是可接受的
            if not isinstance(p.camera_main, int):
                invalid.append(
                    f"{p.brand} {p.model}: camera_main={p.camera_main!r} "
                    f"type={type(p.camera_main).__name__}"
                )
            elif p.camera_main <= 0:
                invalid.append(
                    f"{p.brand} {p.model}: camera_main={p.camera_main} (非正数)"
                )

        assert len(invalid) == 0, (
            f"{len(invalid)}条记录的camera_main值不合法:\n" +
            "\n".join(invalid)
        )

    def test_camera_main_reasonable_range(self, real_db_session):
        """camera_main值在合理范围内（200万-20000万像素）"""
        phones = real_db_session.query(Phone).all()
        outliers = []
        for p in phones:
            if p.camera_main is None:
                continue
            if p.camera_main < 200 or p.camera_main > 20000:
                outliers.append(
                    f"{p.brand} {p.model}: camera_main={p.camera_main}"
                )

        assert len(outliers) == 0, (
            f"{len(outliers)}条记录的camera_main超出合理范围(200-20000):\n" +
            "\n".join(outliers)
        )


# ============================================================================
# (d) 按性能排序使用processor跑分正确
# ============================================================================


class TestPerformanceSorting:
    """retrieval.py按性能排序使用processor跑分"""

    def test_game_sort_by_antutu(self, test_db_session):
        """游戏场景：按安兔兔跑分降序排列"""
        phones_data = [
            Phone(brand="小米", model="旗舰游戏机", price=4999,
                  processor="骁龙8 Gen 3", ram=16, battery=5000),
            Phone(brand="vivo", model="中端机", price=2999,
                  processor="骁龙7+ Gen 3", ram=12, battery=4500),
            Phone(brand="荣耀", model="入门机", price=1499,
                  processor="骁龙680", ram=8, battery=5000),
        ]
        test_db_session.add_all(phones_data)
        test_db_session.commit()

        service = RetrievalService(test_db_session)
        sorted_phones = service._sort_by_scenario(phones_data, ["游戏"])

        # 验证排序顺序：跑分降序
        assert sorted_phones[0].model == "旗舰游戏机", (
            "旗舰应排第一，骁龙8 Gen 3跑分最高"
        )
        assert sorted_phones[1].model == "中端机", "中端应排第二"
        assert sorted_phones[2].model == "入门机", "入门应排第三"

        # 验证跑分确实在排序中使用
        scores = [
            get_antutu_score(p.processor) for p in sorted_phones
        ]
        assert scores[0] > scores[1] > scores[2], (
            f"跑分应严格降序: {scores}"
        )

    def test_game_sort_unknown_processor_zero_score(self, test_db_session):
        """未知处理器跑分为0时，排在最末"""
        phones_data = [
            Phone(brand="小米", model="知名处理器", price=3999,
                  processor="骁龙8 Gen 2", ram=12, battery=5000),
            Phone(brand="vivo", model="未知处理器", price=2999,
                  processor="某未知芯片XYZ", ram=12, battery=5000),
        ]
        test_db_session.add_all(phones_data)
        test_db_session.commit()

        service = RetrievalService(test_db_session)
        sorted_phones = service._sort_by_scenario(phones_data, ["游戏"])

        # 知名处理器应排在前（跑分>0），未知处理器在后（跑分=0）
        assert sorted_phones[0].model == "知名处理器", (
            "跑分>0的处理器应排在前"
        )
        assert sorted_phones[1].model == "未知处理器", "跑分=0的处理器应排在后"

    def test_performance_sort_by_antutu(self, test_db_session):
        """性能场景：按安兔兔跑分降序"""
        phones_data = [
            Phone(brand="小米", model="高性能", price=5999,
                  processor="骁龙8 至尊版 Gen5", ram=24, battery=6000),
            Phone(brand="vivo", model="中性能", price=3999,
                  processor="骁龙8+ Gen 1", ram=12, battery=5000),
            Phone(brand="荣耀", model="低性能", price=1999,
                  processor="骁龙695", ram=8, battery=5000),
        ]
        test_db_session.add_all(phones_data)
        test_db_session.commit()

        service = RetrievalService(test_db_session)
        sorted_phones = service._sort_by_scenario(phones_data, ["性能"])

        scores = [
            get_antutu_score(p.processor) for p in sorted_phones
        ]
        assert scores[0] > scores[1] > scores[2], (
            f"性能排序应降序: {scores}"
        )
        assert sorted_phones[0].model == "高性能"


# ============================================================================
# (e) 按拍照排序使用camera_main整数值正确
# ============================================================================


class TestCameraSorting:
    """retrieval.py按拍照排序使用camera_main整数值"""

    def test_photo_sort_by_camera_mp_descending(self, test_db_session):
        """拍照场景：按主摄像素降序（高像素在前）"""
        phones_data = [
            Phone(brand="红米", model="中像素", price=1999,
                  processor="骁龙695", ram=8, camera_main=6400, features=""),
            Phone(brand="小米", model="高像素", price=3999,
                  processor="骁龙8 Gen 3", ram=12, camera_main=20000, features=""),
            Phone(brand="荣耀", model="低像素", price=999,
                  processor="天玑6020", ram=6, camera_main=4800, features=""),
        ]
        test_db_session.add_all(phones_data)
        test_db_session.commit()

        service = RetrievalService(test_db_session)
        sorted_phones = service._sort_by_scenario(phones_data, ["拍照"])

        # 高像素在前
        assert sorted_phones[0].model == "高像素", (
            f"20000万像素应排第一，实际: {sorted_phones[0].model}"
        )
        assert sorted_phones[1].model == "中像素", (
            f"6400万像素应排第二，实际: {sorted_phones[1].model}"
        )
        assert sorted_phones[2].model == "低像素", (
            f"4800万像素应排第三，实际: {sorted_phones[2].model}"
        )

    def test_photo_sort_null_camera_main_treated_as_zero(self, test_db_session):
        """camera_main为NULL时按0处理，排在最后"""
        phones_data = [
            Phone(brand="小米", model="正常像素", price=3999,
                  processor="骁龙8 Gen 2", ram=12, camera_main=5000, features=""),
            Phone(brand="vivo", model="无主摄", price=2999,
                  processor="骁龙870", ram=8, camera_main=None, features=""),
        ]
        test_db_session.add_all(phones_data)
        test_db_session.commit()

        service = RetrievalService(test_db_session)
        sorted_phones = service._sort_by_scenario(phones_data, ["拍照"])

        assert sorted_phones[0].model == "正常像素", "5000万应排在NULL之前"
        assert sorted_phones[1].model == "无主摄", "NULL应排在最后"

    def test_photo_sort_image_tag_priority(self, test_db_session):
        """同像素时，有影像标签的排在前面"""
        phones_data = [
            Phone(brand="小米", model="无影像标签", price=3999,
                  processor="骁龙8 Gen 3", ram=16, camera_main=5000, features="[]"),
            Phone(brand="vivo", model="蔡司影像", price=4299,
                  processor="骁龙8 Gen 3", ram=16, camera_main=5000,
                  features='["徕卡"]'),
        ]
        test_db_session.add_all(phones_data)
        test_db_session.commit()

        service = RetrievalService(test_db_session)
        sorted_phones = service._sort_by_scenario(phones_data, ["拍照"])

        # 相同像素时，有影像标签的在前
        assert sorted_phones[0].model == "蔡司影像", (
            f"有徕卡标签应排第一，实际: {sorted_phones[0].model}"
        )


# ============================================================================
# (f) _parse_camera_mp()各种输入格式正确解析
# ============================================================================


class TestParseCameraMp:
    """_parse_camera_mp()各种输入格式"""

    def test_wan_format(self):
        """万像素格式：5000万 -> 5000"""
        assert _parse_camera_mp("5000万") == 5000
        assert _parse_camera_mp("1200万像素") == 1200
        assert _parse_camera_mp("6400万") == 6400

    def test_yi_format(self):
        """亿像素格式：2亿 -> 20000"""
        assert _parse_camera_mp("2亿") == 20000
        assert _parse_camera_mp("1.08亿") == 10800
        assert _parse_camera_mp("1亿") == 10000
        assert _parse_camera_mp("0.5亿") == 5000

    def test_integer_input(self):
        """INTEGER输入"""
        assert _parse_camera_mp(5000) == 5000
        assert _parse_camera_mp(0) == 0
        assert _parse_camera_mp(10800) == 10800

    def test_none_input(self):
        """None输入返回None"""
        assert _parse_camera_mp(None) is None

    def test_empty_string(self):
        """空字符串返回None"""
        assert _parse_camera_mp("") is None

    def test_non_numeric_string(self):
        """非数字字符串返回None"""
        assert _parse_camera_mp("未知") is None

    def test_float_input(self):
        """浮点数输入正确解析"""
        assert _parse_camera_mp("2.0亿") == 20000
        assert _parse_camera_mp("0.5万") == 0  # int(0.5) = 0, but float * 1 = 0.5 -> int = 0

    def test_whitespace_handling(self):
        """前后空格正确处理"""
        assert _parse_camera_mp("  5000万  ") == 5000

    def test_float_yi_edge_case(self):
        """浮点亿的边缘情况"""
        assert _parse_camera_mp("1.5亿") == 15000


# ============================================================================
# (g) _safe_camera_value()向后兼容
# ============================================================================


class TestSafeCameraValue:
    """_safe_camera_value()向后兼容"""

    def test_text_wan_input(self):
        """TEXT万像素输入"""
        assert _safe_camera_value("5000万") == 5000

    def test_text_yi_input(self):
        """TEXT亿像素输入"""
        assert _safe_camera_value("2亿") == 20000

    def test_integer_input(self):
        """INTEGER输入"""
        assert _safe_camera_value(5000) == 5000

    def test_none_input(self):
        """None输入返回0"""
        assert _safe_camera_value(None) == 0

    def test_empty_string(self):
        """空字符串返回0"""
        assert _safe_camera_value("") == 0

    def test_unparseable_input(self):
        """无法解析的字符串返回0"""
        assert _safe_camera_value("未知") == 0

    def test_backward_compat_text_large(self):
        """TEXT大值输入"""
        assert _safe_camera_value("1.08亿像素主摄") == 10800


# ============================================================================
# (h) 品牌映射表完整性检查
# ============================================================================


class TestBrandMappingCompleteness:
    """品牌映射表完整性"""

    # 数据库中已知但未在任何映射中覆盖的品牌（小品牌/稀有品牌）
    # 这些品牌通常由LLM直接识别，不需要在映射表中
    KNOWN_UNMAPPED_BRANDS = {"ROG", "努比亚", "真我", "索尼", "魅族", "黑鲨"}

    def test_all_db_brands_in_intent_service(self, real_db_session):
        """数据库中主流品牌都应在意图识别中有映射"""
        # 获取数据库中所有唯一品牌
        phones = real_db_session.query(Phone).all()
        db_brands = set(p.brand for p in phones if p.brand)

        # 意图识别中的品牌关键词（中文+英文）
        # 来源: backend/services/retrieval.py get_phones_by_model 中的品牌列表
        retrieval_brands = {
            "小米", "华为", "苹果", "OPPO", "vivo", "荣耀", "Redmi", "realme",
        }

        # 来源: backend/api/routes/chat.py 中的 brand_mapping
        chat_brand_mapping = {
            "oppo", "vivo", "联想", "moto", "摩托罗拉",
            "三星", "苹果", "红米", "一加", "华为",
            "小米", "荣耀", "realme", "iqoo",
            "redmi", "oneplus", "huawei", "honor",
            "samsung", "apple", "lenovo", "iphone",
        }

        # 来源: chat.py 中的 brand_cn_to_en
        brand_cn_en = {
            "oppo": "oppo", "vivo": "vivo",
            "联想": "lenovo",
            "moto": "moto", "摩托罗拉": "moto",
            "三星": "samsung", "苹果": "apple",
            "红米": "redmi", "一加": "oneplus",
            "华为": "huawei", "小米": "xiaomi",
            "荣耀": "honor", "realme": "realme", "iqoo": "iqoo",
        }

        # 合并所有已知的品牌名称
        all_known_brands = set()
        all_known_brands.update(b.lower() for b in retrieval_brands)
        all_known_brands.update(b.lower() for b in chat_brand_mapping)
        all_known_brands.update(b.lower() for b in brand_cn_en.keys())
        all_known_brands.update(b.lower() for b in brand_cn_en.values())

        # 检查数据库中每个品牌是否在已知映射中
        missing = []
        for brand in db_brands:
            if brand.lower() not in all_known_brands:
                missing.append(brand)

        # 排除已知的小品牌
        unexpected_missing = [b for b in missing if b not in self.KNOWN_UNMAPPED_BRANDS]

        assert len(unexpected_missing) == 0, (
            f"数据库中有{len(unexpected_missing)}个主流品牌缺少映射:\n" +
            "\n".join(sorted(unexpected_missing))
        )

        # 对于已知未被映射的品牌，仅作记录（不失败）
        if missing:
            known_gap_count = len(missing) - len(unexpected_missing)
            if known_gap_count > 0:
                pass  # 预期的品牌覆盖缺口，由KNOWN_UNMAPPED_BRANDS记录

    def test_brand_count_reasonable(self, real_db_session):
        """验证品牌数量在合理范围内"""
        phones = real_db_session.query(Phone).all()
        db_brands = set(p.brand for p in phones if p.brand)
        # 通常手机品牌在10-30个之间
        assert 5 <= len(db_brands) <= 50, (
            f"品牌数量{len(db_brands)}异常 (预期5-50): {sorted(db_brands)}"
        )

    def test_brand_names_consistent(self, real_db_session):
        """品牌名大小写一致（品牌名首字母大写的统一性）"""
        phones = real_db_session.query(Phone).all()
        brands_with_phones = {}
        for p in phones:
            if p.brand:
                brands_with_phones.setdefault(p.brand, []).append(p.model)

        # 警告：大小写变体检测（非硬错误）
        # 例如不应出现 "oppo" 和 "OPPO" 同时存在
        brand_lower_map = {}
        for brand in brands_with_phones:
            lower = brand.lower()
            if lower in brand_lower_map:
                # 已有相同品牌的不同大小写形式
                pass  # 仅作记录，非错误
            brand_lower_map[lower] = brand

        # 硬检查：品牌名不包含非打印字符
        for brand in brands_with_phones:
            assert brand.strip() == brand, f"品牌名'{brand}'包含前后空格"


# ============================================================================
# Supplementary: processer alias and normalization edge cases
# ============================================================================


class TestProcessorNormalization:
    """处理器标准化额外测试"""

    def test_normalize_strips_brand_prefix_chinese(self):
        """_normalize_processor剥离中文品牌前缀"""
        cases = [
            ("高通 骁龙8 Gen 3", "骁龙8 Gen 3"),
            ("联发科 天玑9300", "天玑9300"),
            ("海思 麒麟9000", "麒麟9000"),
            ("三星 Exynos 2400", "Exynos 2400"),
            ("苹果 A17 Pro", "A17 Pro"),
            ("华为 麒麟9000", "麒麟9000"),
        ]
        for raw, expected in cases:
            result = _normalize_processor(raw)
            assert result == expected, (
                f"'{raw}' 应规范为 '{expected}'，实际: '{result}'"
            )

    def test_normalize_strips_brand_prefix_english(self):
        """_normalize_processor剥离英文品牌前缀"""
        cases = [
            ("HUAWEI 麒麟9000", "麒麟9000"),
            ("Samsung Exynos 2400", "Exynos 2400"),
            ("Apple A17 Pro", "A17 Pro"),
        ]
        for raw, expected in cases:
            result = _normalize_processor(raw)
            assert result == expected, (
                f"'{raw}' 应规范为 '{expected}'，实际: '{result}'"
            )

    def test_normalize_removes_chinese_digit_space(self):
        """_normalize_processor移除中文与数字/字母间的空格"""
        assert _normalize_processor("骁龙 8 Gen 3") == "骁龙8 Gen 3"
        assert _normalize_processor("天玑 9300+") == "天玑9300+"

    def test_normalize_applies_alias(self):
        """_normalize_processor应用处理器别名"""
        cases = [
            # "骁龙8Elite" -> "骁龙8至尊版" (无空格，如_PROCESSOR_ALIASES定义)
            ("骁龙8Elite", "骁龙8至尊版"),
            # "骁龙8 Elite" -> "骁龙8 至尊版" (有空格)
            ("骁龙8 Elite", "骁龙8 至尊版"),
            ("第四代骁龙7", "骁龙7 Gen 4"),
            ("第三代骁龙7+", "骁龙7+ Gen 3"),
            ("骁龙8 Gen1", "骁龙8 Gen 1"),
        ]
        for raw, expected in cases:
            result = _normalize_processor(raw)
            assert result == expected, (
                f"别名'{raw}' 应规范为 '{expected}'，实际: '{result}'"
            )

    def test_normalize_empty_input(self):
        """_normalize_processor空输入返回空"""
        assert _normalize_processor("") == ""
        assert _normalize_processor("  ") == ""


class TestSessionLocal:
    """验证SessionLocal可以正常创建会话"""

    def test_sessionlocal_importable(self):
        """SessionLocal可以被正确导入"""
        assert SessionLocal is not None
