from backend.models.domain import SessionLocal
from backend.services.session import SessionService
from backend.services.intent import IntentService
from backend.services.recommend import RecommendService


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 服务实例 - 单例模式
_session_service: SessionService = None
_intent_service: IntentService = None
_recommend_service: RecommendService = None


def get_session_service() -> SessionService:
    """获取会话服务实例（单例）"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service


def get_intent_service() -> IntentService:
    """获取意图识别服务实例（单例）"""
    global _intent_service
    if _intent_service is None:
        _intent_service = IntentService()
    return _intent_service


def get_recommend_service() -> RecommendService:
    """获取推荐服务实例（单例）"""
    global _recommend_service
    if _recommend_service is None:
        _recommend_service = RecommendService()
    return _recommend_service
