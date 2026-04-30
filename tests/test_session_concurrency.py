"""
会话服务并发测试 - 验证线程安全
"""
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.services.session import SessionService, sessions, _sessions_lock


class TestSessionConcurrency:
    """会话并发安全测试"""

    def setup_method(self):
        """每个测试前清空会话"""
        with _sessions_lock:
            sessions.clear()

    def test_concurrent_create_sessions(self):
        """测试并发创建会话"""
        service = SessionService()
        session_ids = []
        errors = []

        def create_session():
            try:
                sid = service.create_session()
                session_ids.append(sid)
            except Exception as e:
                errors.append(str(e))

        # 并发创建100个会话
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_session) for _ in range(100)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"并发创建会话出错: {errors}"
        assert len(session_ids) == 100
        assert len(set(session_ids)) == 100, "会话ID应该唯一"

    def test_concurrent_add_messages(self):
        """测试并发添加消息到同一会话"""
        service = SessionService()
        session_id = service.create_session()
        errors = []

        def add_message(i):
            try:
                service.add_message(session_id, "user", f"message_{i}")
            except Exception as e:
                errors.append(str(e))

        # 并发添加15条消息（不超过MAX_MESSAGES=20）
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(add_message, i) for i in range(15)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"并发添加消息出错: {errors}"
        messages = service.get_messages(session_id)
        assert len(messages) == 15

    def test_concurrent_read_write(self):
        """测试并发读写"""
        service = SessionService()
        session_id = service.create_session()
        errors = []

        def write_operation(i):
            try:
                service.add_message(session_id, "user", f"write_{i}")
            except Exception as e:
                errors.append(str(e))

        def read_operation():
            try:
                service.get_messages(session_id)
            except Exception as e:
                errors.append(str(e))

        # 混合读写操作
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(25):
                futures.append(executor.submit(write_operation, i))
                futures.append(executor.submit(read_operation))
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"并发读写出错: {errors}"

    def test_cleanup_expired_sessions_thread_safe(self):
        """测试清理过期会话的线程安全"""
        service = SessionService()

        # 创建多个会话
        for _ in range(10):
            service.create_session()

        errors = []

        def cleanup():
            try:
                service.cleanup_expired_sessions()
            except Exception as e:
                errors.append(str(e))

        def add_more():
            try:
                sid = service.create_session()
                service.add_message(sid, "user", "test")
            except Exception as e:
                errors.append(str(e))

        # 并发执行清理和添加
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(cleanup))
                futures.append(executor.submit(add_more))
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"并发清理出错: {errors}"
