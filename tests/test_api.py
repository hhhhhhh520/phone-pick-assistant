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
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


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


def test_get_phone(client):
    response = client.get("/api/phones/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "brand" in data
    assert "model" in data
    assert "price" in data


def test_get_phone_not_found(client):
    response = client.get("/api/phones/99999")
    assert response.status_code == 404
