"""Session统计端点测试"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.services.session import sessions, _sessions_lock


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """每个测试前后清空会话"""
    with _sessions_lock:
        sessions.clear()
    yield
    with _sessions_lock:
        sessions.clear()


class TestSessionStats:
    """Session统计端点测试"""

    def test_stats_empty_sessions(self, client):
        """无会话时统计为0"""
        response = client.get("/stats/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 0
        assert data["total_messages"] == 0
        assert data["avg_messages_per_session"] == 0

    def test_stats_with_sessions(self, client):
        """有会话时统计正确"""
        # 创建会话
        from backend.services.session import SessionService
        session_service = SessionService()

        # 创建2个会话，各添加消息
        sid1 = session_service.create_session()
        session_service.add_message(sid1, "user", "hello")
        session_service.add_message(sid1, "assistant", "hi")

        sid2 = session_service.create_session()
        session_service.add_message(sid2, "user", "test")

        # 检查统计
        response = client.get("/stats/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 2
        assert data["total_messages"] == 3
        assert data["avg_messages_per_session"] == 1.5

    def test_stats_after_cleanup(self, client):
        """清理过期会话后统计更新"""
        from backend.services.session import SessionService
        from datetime import datetime, timedelta

        session_service = SessionService()

        # 创建会话
        sid = session_service.create_session()
        session_service.add_message(sid, "user", "test")

        # 手动设置过期时间
        from backend.services.session import sessions, _sessions_lock
        with _sessions_lock:
            sessions[sid].last_activity = datetime.now() - timedelta(minutes=60)

        # 清理过期会话
        session_service.cleanup_expired_sessions()

        # 检查统计
        response = client.get("/stats/sessions")
        data = response.json()
        assert data["total_sessions"] == 0

    def test_stats_message_count_limit(self, client):
        """消息数量限制正确"""
        from backend.services.session import SessionService, MAX_STORED_MESSAGES

        session_service = SessionService()
        sid = session_service.create_session()

        # 添加超过限制的消息
        for i in range(MAX_STORED_MESSAGES + 5):
            session_service.add_message(sid, "user", f"msg{i}")

        # 检查统计 - 消息数不应超过限制
        response = client.get("/stats/sessions")
        data = response.json()
        assert data["total_messages"] == MAX_STORED_MESSAGES
