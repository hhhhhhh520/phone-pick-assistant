"""测试型号匹配逻辑"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.domain import Phone, Base
from backend.services.retrieval import RetrievalService


@pytest.fixture
def db_session():
    """创建测试数据库"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 添加测试数据
    test_phones = [
        Phone(brand="小米", model="小米14", price=3999, image_url="http://example.com/xiaomi14.jpg"),
        Phone(brand="小米", model="小米14 Ultra", price=6499, image_url="http://example.com/xiaomi14ultra.jpg"),
        Phone(brand="小米", model="Redmi Note 14", price=1199, image_url="http://example.com/redmi14.jpg"),
        Phone(brand="小米", model="Redmi Note 14 Pro+", price=1999, image_url=None),
        Phone(brand="华为", model="P60", price=4988, image_url="http://example.com/p60.jpg"),
        Phone(brand="华为", model="P60 Pro", price=5988, image_url="http://example.com/p60pro.jpg"),
        Phone(brand="苹果", model="iPhone 15", price=5999, image_url="http://example.com/iphone15.jpg"),
        Phone(brand="苹果", model="iPhone 15 Pro", price=7999, image_url="http://example.com/iphone15pro.jpg"),
        Phone(brand="OPPO", model="Find X6", price=4499, image_url=None),
        Phone(brand="vivo", model="X90", price=3699, image_url=None),
    ]
    db.add_all(test_phones)
    db.commit()
    yield db
    db.close()


def test_exact_model_match(db_session):
    """测试精确型号匹配：'小米14'应匹配到'小米14'，而非'Redmi Note 14'"""
    service = RetrievalService(db_session)
    phones = service.get_phones_by_model(["小米14"])

    assert len(phones) == 1
    assert phones[0].model == "小米14"
    assert phones[0].price == 3999
    # 关键验证：不应匹配到 Redmi Note 14
    assert "Redmi" not in phones[0].model


def test_partial_model_match(db_session):
    """测试子串匹配：'小米14'作为子串应能匹配到'小米14 Ultra'（当精确匹配失败时）"""
    service = RetrievalService(db_session)
    # 删除小米14，测试是否能匹配到小米14 Ultra
    db_session.query(Phone).filter(Phone.model == "小米14").delete()
    db_session.commit()

    phones = service.get_phones_by_model(["小米14"])
    assert len(phones) == 1
    assert phones[0].model == "小米14 Ultra"


def test_brand_core_model_match(db_session):
    """测试同品牌核心型号匹配：'Redmi Note 14'应正确匹配"""
    service = RetrievalService(db_session)
    phones = service.get_phones_by_model(["Redmi Note 14"])

    assert len(phones) == 1
    assert phones[0].model == "Redmi Note 14"
    assert phones[0].price == 1199


def test_multiple_models_comparison(db_session):
    """测试多型号对比：'小米14'和'华为P60'"""
    service = RetrievalService(db_session)
    phones = service.get_phones_by_model(["小米14", "华为P60"])

    assert len(phones) == 2
    models = [p.model for p in phones]
    assert "小米14" in models
    # 华为P60可能匹配到P60或P60 Pro
    assert any("P60" in m for m in models)


def test_iphone_model_match(db_session):
    """测试iPhone型号匹配"""
    service = RetrievalService(db_session)
    phones = service.get_phones_by_model(["iPhone 15"])

    assert len(phones) == 1
    assert phones[0].model == "iPhone 15"


def test_nonexistent_model(db_session):
    """测试不存在型号：应返回空列表"""
    service = RetrievalService(db_session)
    phones = service.get_phones_by_model(["不存在型号"])

    assert len(phones) == 0


def test_model_with_price_filter(db_session):
    """测试型号匹配自动过滤无效价格"""
    # 添加一个价格为0的记录
    db_session.add(Phone(brand="小米", model="小米14", price=0, image_url=None))
    db_session.commit()

    service = RetrievalService(db_session)
    phones = service.get_phones_by_model(["小米14"])

    # 应返回有效价格的记录（3999），而非价格为0的
    assert len(phones) == 1
    assert phones[0].price == 3999


def test_model_match_priority(db_session):
    """测试匹配优先级：精确匹配优先于子串匹配"""
    service = RetrievalService(db_session)

    # 同时存在"小米14"和"小米14 Ultra"，应优先返回"小米14"
    phones = service.get_phones_by_model(["小米14"])
    assert phones[0].model == "小米14"
    assert phones[0].price == 3999  # 精确匹配的价格