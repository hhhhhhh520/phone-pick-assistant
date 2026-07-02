"""
健康检查端点测试 - tests/test_health.py

测试场景：
1. 所有组件正常 -> status=healthy
2. 数据库异常 -> status=unhealthy
3. LLM异常 -> status=degraded
4. 响应格式验证
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app, _reset_health_cache, _set_llm_health


@pytest.fixture(autouse=True)
def reset_health_cache():
    """每个测试前重置健康检查缓存"""
    _reset_health_cache()
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthResponseFormat:
    """测试健康检查响应格式"""

    def test_health_returns_200(self, client):
        """健康检查应返回200状态码"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_has_required_fields(self, client):
        """响应必须包含顶层字段：status, latency_ms, components"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "latency_ms" in data
        assert "components" in data

    def test_health_status_valid_values(self, client):
        """status字段只能是 healthy, degraded, unhealthy 之一"""
        response = client.get("/health")
        data = response.json()

        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_latency_is_number(self, client):
        """latency_ms 必须是数字类型"""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["latency_ms"], (int, float))
        assert data["latency_ms"] >= 0

    def test_health_components_structure(self, client):
        """components 必须包含 database 和 llm"""
        response = client.get("/health")
        data = response.json()

        components = data["components"]
        assert "database" in components
        assert "llm" in components

    def test_database_component_fields(self, client):
        """数据库组件字段验证"""
        response = client.get("/health")
        data = response.json()

        db = data["components"]["database"]
        assert db["status"] in ["connected", "error"]
        if db["status"] == "connected":
            assert "latency_ms" in db
            assert isinstance(db["latency_ms"], (int, float))
        elif db["status"] == "error":
            assert "error" in db

    def test_llm_component_fields(self, client):
        """LLM组件字段验证"""
        _set_llm_health("available", model="deepseek-chat")
        response = client.get("/health")
        data = response.json()

        llm = data["components"]["llm"]
        assert llm["status"] in ["available", "unavailable", "unknown", "error"]
        assert "model" in llm
        if llm["status"] in ("unavailable", "error"):
            assert "error" in llm


class TestHealthAllComponentsHealthy:
    """测试所有组件正常的场景"""

    @patch("backend.models.domain.SessionLocal")
    def test_all_healthy_returns_healthy_status(self, mock_session_local, client):
        """所有组件正常时，status应为healthy"""
        # Mock 数据库连接正常
        mock_session = MagicMock()
        mock_session.execute.return_value = None
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_local.return_value = mock_session

        # 设置 LLM 健康缓存（后台刷新结果，请求读缓存）(ISSUE-042)
        _set_llm_health("available", model="deepseek-chat")

        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy", f"所有组件正常时status应为healthy，实际为 {data['status']}"

    def test_database_connected_has_latency(self, client):
        """数据库连接正常时应包含latency_ms"""
        response = client.get("/health")
        data = response.json()

        db = data["components"]["database"]
        if db["status"] == "connected":
            assert "latency_ms" in db
            assert db["latency_ms"] is not None
            assert db["latency_ms"] >= 0

    def test_llm_available_shows_model(self, client):
        """LLM可用时应显示模型名称"""
        _set_llm_health("available", model="deepseek-chat")
        response = client.get("/health")
        data = response.json()

        llm = data["components"]["llm"]
        assert "model" in llm
        assert llm["model"] is not None


class TestHealthDatabaseError:
    """测试数据库异常场景"""

    @patch("backend.models.domain.SessionLocal")
    def test_database_error_returns_unhealthy(self, mock_session_local, client):
        """数据库异常时，status应为unhealthy"""
        # 模拟数据库连接失败
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Connection refused")
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_local.return_value = mock_session

        response = client.get("/health")
        data = response.json()

        assert data["status"] == "unhealthy"
        assert data["components"]["database"]["status"] == "error"
        assert "error" in data["components"]["database"]

    @patch("backend.models.domain.SessionLocal")
    def test_database_error_contains_error_message(self, mock_session_local, client):
        """数据库错误时应包含错误信息"""
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database locked")
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_local.return_value = mock_session

        response = client.get("/health")
        data = response.json()

        db = data["components"]["database"]
        assert db["status"] == "error"
        assert "Database locked" in db["error"]

    @patch("backend.models.domain.SessionLocal")
    def test_database_timeout_treated_as_error(self, mock_session_local, client):
        """数据库超时应视为错误"""
        mock_session = MagicMock()
        mock_session.execute.side_effect = TimeoutError("Connection timeout")
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_local.return_value = mock_session

        response = client.get("/health")
        data = response.json()

        assert data["components"]["database"]["status"] == "error"


class TestHealthLLMError:
    """测试LLM异常场景"""

    def test_llm_error_returns_degraded(self, client):
        """LLM异常但数据库正常时，status应为degraded"""
        _set_llm_health("unavailable", model="deepseek-chat", error="API Key无效或已过期")

        response = client.get("/health")
        data = response.json()

        # 数据库正常时，LLM异常应该是degraded
        if data["components"]["database"]["status"] == "connected":
            assert data["status"] == "degraded"

    def test_llm_connection_error(self, client):
        """LLM连接失败"""
        _set_llm_health("unavailable", model="deepseek-chat", error="无法连接到API服务")

        response = client.get("/health")
        data = response.json()

        llm = data["components"]["llm"]
        assert llm["status"] == "unavailable"
        assert "无法连接" in llm["error"]

    def test_llm_timeout_error(self, client):
        """LLM超时错误"""
        _set_llm_health("unavailable", model="deepseek-chat", error="API连接超时")

        response = client.get("/health")
        data = response.json()

        llm = data["components"]["llm"]
        assert llm["status"] == "unavailable"
        assert "超时" in llm["error"]

    def test_llm_auth_error(self, client):
        """LLM认证错误"""
        _set_llm_health("unavailable", model="deepseek-chat", error="API Key无效或已过期")

        response = client.get("/health")
        data = response.json()

        llm = data["components"]["llm"]
        assert llm["status"] == "unavailable"
        assert "API Key" in llm["error"]


class TestHealthPartialDegradation:
    """测试部分降级场景"""

    @patch("backend.models.domain.SessionLocal")
    def test_both_components_error_returns_unhealthy(
        self, mock_session_local, client
    ):
        """数据库和LLM都异常时，status应为unhealthy"""
        # 模拟数据库错误
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("DB Error")
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_local.return_value = mock_session

        # 模拟LLM错误（设置缓存）
        _set_llm_health("unavailable", model="deepseek-chat", error="API Error")

        response = client.get("/health")
        data = response.json()

        assert data["status"] == "unhealthy"

    def test_llm_rate_limit_treated_as_available(self, client):
        """LLM速率限制应视为可用（degraded而非unhealthy）"""
        _set_llm_health("available", model="deepseek-chat", error="API速率受限，但服务可达")

        response = client.get("/health")
        data = response.json()

        llm = data["components"]["llm"]
        assert llm["status"] == "available"


class TestHealthLatencyMeasurement:
    """测试延迟测量"""

    def test_total_latency_reasonable(self, client):
        """总延迟应在合理范围内（<10秒）"""
        response = client.get("/health")
        data = response.json()

        # 健康检查不应超过10秒
        assert data["latency_ms"] < 10000

    @patch("backend.models.domain.SessionLocal")
    def test_database_latency_measured(self, mock_session_local, client):
        """数据库延迟应被正确测量"""
        mock_session = MagicMock()
        mock_session.execute.return_value = None
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_local.return_value = mock_session

        response = client.get("/health")
        data = response.json()

        db = data["components"]["database"]
        assert db["status"] == "connected", f"Mock数据库应显示connected，实际为 {db['status']}"
        assert db["latency_ms"] is not None, "数据库延迟不应为 None"
        assert db["latency_ms"] >= 0, f"数据库延迟应 >= 0，实际为 {db['latency_ms']}"


class TestHealthStatusConsistency:
    """测试状态一致性"""

    def test_status_matches_component_states(self, client):
        """整体状态应与组件状态一致"""
        response = client.get("/health")
        data = response.json()

        db_healthy = data["components"]["database"]["status"] == "connected"
        llm_healthy = data["components"]["llm"]["status"] == "available"

        if db_healthy and llm_healthy:
            assert data["status"] == "healthy"
        elif db_healthy:
            # 数据库正常但LLM异常
            assert data["status"] in ["degraded", "healthy"]
        else:
            # 数据库异常
            assert data["status"] == "unhealthy"


class TestHealthNonBlocking:
    """测试 /health 不阻塞等待 LLM (ISSUE-042)

    改后台异步刷新后，/health 请求应读缓存立即返回，不等待 LLM 响应。
    """

    def test_health_does_not_call_llm_service(self, client):
        """/health 请求不应同步调用 LLMService.health_check（读缓存）"""
        with patch("backend.services.llm.LLMService.health_check", new_callable=AsyncMock) as mock_check:
            _set_llm_health("available", model="deepseek-chat")
            response = client.get("/health")
            # /health 不应同步调 LLM（后台任务才调）
            mock_check.assert_not_called()
            assert response.status_code == 200

    def test_health_response_fast_without_llm_call(self, client):
        """无 LLM 调用时，/health 应快速返回（<500ms，仅 DB 检查）"""
        _set_llm_health("available", model="deepseek-chat")
        response = client.get("/health")
        data = response.json()
        # 仅 DB 检查 + 读缓存，应在 500ms 内
        assert data["latency_ms"] < 500, f"/health 应快速返回，实际 {data['latency_ms']}ms"

    def test_health_returns_unknown_when_cache_not_refreshed(self, client):
        """启动初期 LLM 缓存未刷新时，status 为 unknown（不阻塞等待）"""
        # _reset_health_cache 已在 fixture 重置 _llm_health 为 unknown
        response = client.get("/health")
        data = response.json()
        llm = data["components"]["llm"]
        assert llm["status"] == "unknown"
        # 仍应快速返回，不等待 LLM
        assert data["latency_ms"] < 500
