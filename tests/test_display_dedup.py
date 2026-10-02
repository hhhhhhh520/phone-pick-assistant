"""
W4 品牌去重 + Xperia 重复行清理守卫测试 (2026-10-02, ISSUE-050)

问题一：f"{brand} {model}" 拼接在 model 已含品牌前缀时输出重复品牌
（"真我 真我Neo8"、"苹果 苹果iPhone 15"），并进入 LLM prompt、推荐匹配结果与
前端 aria-label。修复：domain.Phone.display_name 属性统一去重（model 已含品牌
则原样使用，否则 brand + model 拼一次），三处后端展示点接入。

问题二：索尼 Xperia PRO-I 同一台手机 3 行（1233 干净名 / 1738 垃圾名重复 /
1748 price=0 不可见且芯片错）。修复：保留 1233（W1 修复后芯片已正确、
model 名干净、价格可见），删除 1738 与 1748；删后 DB=API=351，price<=0 归零。

注意：chat.py:227 的 brand+model 拼接是**匹配用的检索 haystack，刻意不动**；
image_loader/update_images 的 brand+model 是**映射键**，非展示，不改。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.domain import Phone


class TestDisplayNameProperty:
    """Phone.display_name：model 含品牌前缀则不重复拼接"""

    def test_model_with_brand_prefix_not_doubled(self):
        p = Phone(brand="真我", model="真我Neo8")
        assert p.display_name == "真我Neo8"

    def test_model_without_brand_gets_brand_once(self):
        p = Phone(brand="索尼", model="Xperia PRO-I")
        assert p.display_name == "索尼 Xperia PRO-I"

    def test_model_equal_to_brand(self):
        p = Phone(brand="真我", model="真我")
        assert p.display_name == "真我"

    def test_empty_brand_keeps_model(self):
        p = Phone(brand="", model="Neo8")
        assert p.display_name == "Neo8"

    def test_empty_model_returns_brand(self):
        p = Phone(brand="真我", model="")
        assert p.display_name == "真我"


class TestCallSites:
    """三处接入点：LLM prompt / 推荐匹配 / 展示结果"""

    def test_format_phone_no_double_brand(self):
        from backend.services.recommend import RecommendService
        svc = object.__new__(RecommendService)  # 跳过 __init__（仅格式化，不触 LLM）
        p = Phone(brand="真我", model="真我Neo8", price=2399, ram=12, battery=8000)
        line = svc._format_phone(p)
        # _format_phone 返回逗号拼接的单行，首段为展示名
        assert line.split(",")[0] == "真我Neo8"
        assert "真我 真我" not in line

    def test_match_from_candidates_no_double_brand(self):
        from backend.services.model_parser import ModelParserService
        parser = object.__new__(ModelParserService)
        phones = [Phone(brand="真我", model="真我Neo8")]
        matched = parser._match_from_candidates("推荐 真我Neo8 这款", phones)
        assert matched == ["真我Neo8"]


@pytest.fixture
def real_db_session():
    """连接真实数据库（与 test_data_completeness.real_db_session 同惯例）"""
    import backend.config
    settings = backend.config.get_settings()
    db_url = settings.database_url
    if db_url.startswith("sqlite:///./"):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rel_path = db_url.replace("sqlite:///./", "")
        abs_path = os.path.join(project_root, rel_path)
        db_url = f"sqlite:///{abs_path}"

    engine = create_engine(db_url)
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        assert "phones" in inspector.get_table_names(), (
            f"phones表不存在，数据库路径: {db_url}"
        )
        Session = sessionmaker(bind=engine)
        db = Session()
        yield db
        db.close()
    finally:
        engine.dispose()


class TestXperiaDedup:
    """重复行清理：保留 1233，删除 1738/1748"""

    def test_keeper_row_intact(self, real_db_session):
        p = real_db_session.query(Phone).filter(Phone.id == 1233).one_or_none()
        assert p is not None, "保留行 id=1233 不存在"
        assert p.model == "Xperia PRO-I"
        assert p.processor == "骁龙888"
        assert p.price == 10999
        assert p.display_name == "索尼 Xperia PRO-I"

    def test_duplicates_deleted(self, real_db_session):
        for gone_id in (1738, 1748):
            row = real_db_session.query(Phone).filter(Phone.id == gone_id).one_or_none()
            assert row is None, f"id={gone_id} 应已删除，仍存在: {row}"

    def test_total_and_price_filter_consistent(self, real_db_session):
        # 总行数用区间断言（同 test_data_completeness 惯例），避免正常增删机型误报回归；
        # 删除本身的证明由 test_duplicates_deleted 承担，本测只锁定不变量
        total = real_db_session.query(Phone).count()
        assert 300 <= total <= 500, f"总行数应处 300-500 区间（ISSUE-050 时点为 351），实际 {total}"
        nonpositive = real_db_session.query(Phone).filter(Phone.price <= 0).count()
        assert nonpositive == 0, f"price<=0 应为 0（API 口径差随之消失），实际 {nonpositive}"
