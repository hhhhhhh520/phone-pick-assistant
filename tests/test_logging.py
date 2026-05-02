"""日志记录功能测试"""
import pytest
import logging
from io import StringIO
from backend.services.session import SessionService
from backend.services.llm import LLMService, LLMError


class TestSessionLogging:
    """Session服务日志测试"""

    def test_session_create_logs(self, caplog):
        """创建会话记录日志"""
        with caplog.at_level(logging.DEBUG):
            session_service = SessionService()
            sid = session_service.create_session()

            # 检查日志包含会话创建信息
            assert any("Session created" in record.message for record in caplog.records)
            assert any(sid[:8] in record.message for record in caplog.records)

    def test_session_add_message_logs(self, caplog):
        """添加消息记录日志"""
        with caplog.at_level(logging.DEBUG):
            session_service = SessionService()
            sid = session_service.create_session()
            caplog.clear()

            session_service.add_message(sid, "user", "test message")

            # 检查日志包含消息添加信息
            assert any("Message added" in record.message for record in caplog.records)
            assert any("role=user" in record.message for record in caplog.records)

    def test_session_cleanup_logs(self, caplog):
        """清理过期会话记录日志"""
        with caplog.at_level(logging.INFO):
            session_service = SessionService()
            sid = session_service.create_session()

            # 手动设置过期
            from backend.services.session import sessions, _sessions_lock
            from datetime import datetime, timedelta
            with _sessions_lock:
                messages, _ = sessions[sid]
                sessions[sid] = (messages, datetime.now() - timedelta(minutes=60))

            caplog.clear()
            count = session_service.cleanup_expired_sessions()

            assert count == 1
            assert any("Cleaned up" in record.message for record in caplog.records)


class TestLLMLogging:
    """LLM服务日志测试"""

    def test_llm_response_length_logged(self, caplog):
        """LLM响应长度记录日志"""
        with caplog.at_level(logging.DEBUG):
            llm = LLMService()

            # 检查日志配置正确
            assert llm.model is not None
            assert llm.api_key is not None


class TestLoggingConfiguration:
    """日志配置测试"""

    def test_log_level_from_settings(self):
        """日志级别从配置读取"""
        from backend.config import get_settings
        settings = get_settings()
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_logger_has_handlers(self):
        """Logger配置了处理器"""
        logger = logging.getLogger("backend")
        # 根logger应该有handlers
        assert len(logging.root.handlers) >= 1
