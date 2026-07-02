import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "手机选购助手" in data["message"]


def test_health(client):
    """测试健康检查端点返回格式和降级支持"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    # 验证顶层字段
    assert "status" in data
    assert "latency_ms" in data
    assert "components" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert isinstance(data["latency_ms"], (int, float))

    # 验证组件结构
    components = data["components"]
    assert "database" in components
    assert "llm" in components

    # 验证数据库组件
    db = components["database"]
    assert db["status"] in ["connected", "error"]
    if db["status"] == "connected":
        assert "latency_ms" in db

    # 验证LLM组件（status 可能是 available/unavailable/unknown，由后台缓存刷新）
    llm = components["llm"]
    assert llm["status"] in ["available", "unavailable", "unknown", "error"]
    assert "model" in llm

    # 验证状态一致性
    db_healthy = db["status"] == "connected"
    llm_healthy = llm["status"] == "available"

    if db_healthy and llm_healthy:
        assert data["status"] == "healthy"
    elif db_healthy:
        # DB 正常但 LLM 非 available（unavailable/unknown/error）→ degraded
        assert data["status"] == "degraded"
    else:
        assert data["status"] == "unhealthy"


def test_list_phones(client):
    response = client.get("/api/phones")
    assert response.status_code == 200
    data = response.json()
    assert "phones" in data
    assert "total" in data
    assert isinstance(data["phones"], list)


def test_list_phones_with_brand_filter(client):
    response = client.get("/api/phones?brand=Apple")
    assert response.status_code == 200
    data = response.json()
    for phone in data["phones"]:
        assert phone["brand"] == "Apple"


def test_list_phones_with_price_filter(client):
    response = client.get("/api/phones?min_price=3000&max_price=5000")
    assert response.status_code == 200
    data = response.json()
    for phone in data["phones"]:
        assert 3000 <= phone["price"] <= 5000


def test_list_phones_includes_imageurl(client):
    """列表接口应返回 imageUrl 字段供前端卡片展示 (ISSUE-041)"""
    response = client.get("/api/phones?limit=5")
    assert response.status_code == 200
    phones = response.json()["phones"]
    assert len(phones) > 0
    for phone in phones:
        assert "imageUrl" in phone, "列表接口应包含 imageUrl 字段"


def test_list_phones_sort_price_asc(client):
    """sort=price_asc 应按价格升序 (ISSUE-043)"""
    response = client.get("/api/phones?sort=price_asc&limit=10")
    assert response.status_code == 200
    prices = [p["price"] for p in response.json()["phones"]]
    assert prices == sorted(prices), f"应升序，实际 {prices}"


def test_list_phones_sort_price_desc(client):
    """sort=price_desc 应按价格降序 (ISSUE-043)"""
    response = client.get("/api/phones?sort=price_desc&limit=10")
    assert response.status_code == 200
    prices = [p["price"] for p in response.json()["phones"]]
    assert prices == sorted(prices, reverse=True), f"应降序，实际 {prices}"


def test_list_phones_invalid_sort_returns_422(client):
    """无效 sort 值应返回 422 (ISSUE-043)"""
    response = client.get("/api/phones?sort=invalid")
    assert response.status_code == 422


def test_get_phone(client):
    """测试获取手机详情 - 使用数据库中实际存在的ID"""
    # 先获取手机列表，取第一个有效ID
    list_response = client.get("/api/phones?limit=1")
    assert list_response.status_code == 200
    phones = list_response.json()["phones"]
    assert len(phones) > 0, "数据库中至少应有一款手机"

    phone_id = phones[0]["id"]
    response = client.get(f"/api/phones/{phone_id}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "brand" in data
    assert "model" in data
    assert "price" in data


def test_get_phone_not_found(client):
    response = client.get("/api/phones/99999")
    assert response.status_code == 404
