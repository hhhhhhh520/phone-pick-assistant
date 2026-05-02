"""
测试依赖注入 - ISSUE-006 验证
验证服务实例化策略一致性
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.dependencies import (
    get_session_service,
    get_intent_service,
    get_recommend_service,
)
from backend.services.session import SessionService
from backend.services.intent import IntentService
from backend.services.recommend import RecommendService


class TestDependencyInjection:
    """测试依赖注入函数"""

    def test_get_session_service_returns_singleton(self):
        """验证 get_session_service 返回单例"""
        service1 = get_session_service()
        service2 = get_session_service()

        assert service1 is service2, "SessionService 应该是单例"
        assert isinstance(service1, SessionService)

    def test_get_intent_service_returns_singleton(self):
        """验证 get_intent_service 返回单例"""
        service1 = get_intent_service()
        service2 = get_intent_service()

        assert service1 is service2, "IntentService 应该是单例"
        assert isinstance(service1, IntentService)

    def test_get_recommend_service_returns_singleton(self):
        """验证 get_recommend_service 返回单例"""
        service1 = get_recommend_service()
        service2 = get_recommend_service()

        assert service1 is service2, "RecommendService 应该是单例"
        assert isinstance(service1, RecommendService)

    def test_all_services_are_different_instances(self):
        """验证不同服务是不同的实例"""
        session_service = get_session_service()
        intent_service = get_intent_service()
        recommend_service = get_recommend_service()

        assert session_service is not intent_service
        assert session_service is not recommend_service
        assert intent_service is not recommend_service
