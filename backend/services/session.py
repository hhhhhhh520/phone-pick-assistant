"""
会话管理服务 - 内存存储
"""
import uuid
import threading
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from backend.models.schemas import UserProfile, IntentResult

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """会话数据结构"""
    messages: List[Dict] = field(default_factory=list)
    user_profile: Optional[UserProfile] = None


@dataclass
class SessionData:
    """会话完整数据，包含活动时间"""
    session: Session = field(default_factory=Session)
    last_activity: datetime = field(default_factory=datetime.now)


# 会话存储：session_id -> SessionData
sessions: Dict[str, SessionData] = {}
# 线程锁，保护并发访问
_sessions_lock = threading.Lock()

# 存储层消息上限（高于LLM传入层，保留完整历史用于追溯）
# LLM传入层使用 config.max_context_messages (默认10)
MAX_STORED_MESSAGES = 50
# 会话过期时间（30分钟不活跃）
SESSION_EXPIRE_MINUTES = 30


class SessionService:
    def __init__(self):
        pass

    def _update_activity(self, session_id: str) -> None:
        """更新会话最后活动时间（内部方法，调用者需持有锁）"""
        if session_id in sessions:
            sessions[session_id].last_activity = datetime.now()

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        with _sessions_lock:
            sessions[session_id] = SessionData(session=Session(), last_activity=datetime.now())
        logger.debug(f"Session created: {session_id[:8]}...")
        return session_id

    def get_session(self, session_id: str) -> Optional[List[Dict]]:
        """获取会话历史"""
        with _sessions_lock:
            data = sessions.get(session_id)
            if data:
                return data.session.messages
            return None

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息到会话"""
        with _sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = SessionData(session=Session(), last_activity=datetime.now())

            session = sessions[session_id].session
            session.messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            # 保留最近的消息（存储层上限）
            if len(session.messages) > MAX_STORED_MESSAGES:
                session.messages = session.messages[-MAX_STORED_MESSAGES:]

            sessions[session_id].last_activity = datetime.now()

        logger.debug(f"Message added to session {session_id[:8]}...: role={role}, length={len(content)}")

    def get_messages(self, session_id: str) -> List[Dict]:
        """获取会话消息列表（用于LLM上下文）"""
        with _sessions_lock:
            data = sessions.get(session_id)
            if data:
                messages = data.session.messages
            else:
                messages = []
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        with _sessions_lock:
            return session_id in sessions

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话，返回清理数量"""
        expired_count = 0
        expire_threshold = datetime.now() - timedelta(minutes=SESSION_EXPIRE_MINUTES)
        with _sessions_lock:
            expired_sessions = [
                sid for sid, data in sessions.items()
                if data.last_activity < expire_threshold
            ]
            for sid in expired_sessions:
                del sessions[sid]
                expired_count += 1

        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")

        return expired_count

    # ========== 用户需求状态管理 ==========

    def get_profile(self, session_id: str) -> Optional[UserProfile]:
        """
        获取用户需求状态。

        Args:
            session_id: 会话ID

        Returns:
            UserProfile 如果存在，否则 None
        """
        with _sessions_lock:
            data = sessions.get(session_id)
            if data:
                return data.session.user_profile
            return None

    def save_profile(self, session_id: str, profile: UserProfile) -> None:
        """
        保存用户需求状态。

        Args:
            session_id: 会话ID
            profile: 用户需求状态
        """
        with _sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = SessionData(session=Session(), last_activity=datetime.now())

            sessions[session_id].session.user_profile = profile
            sessions[session_id].last_activity = datetime.now()

        logger.debug(f"Profile saved for session {session_id[:8]}...")

    def update_profile(self, session_id: str, intent_result: IntentResult) -> UserProfile:
        """
        根据意图识别结果增量更新用户需求状态。

        如果会话没有现有状态，创建新状态。
        如果已有状态，增量合并。

        Args:
            session_id: 会话ID
            intent_result: 意图识别结果

        Returns:
            UserProfile: 更新后的用户需求状态
        """
        with _sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = SessionData(session=Session(), last_activity=datetime.now())

            current_profile = sessions[session_id].session.user_profile
            if current_profile is None:
                current_profile = UserProfile()

            # 使用 UserProfile 的 update_from_intent 方法
            updated_profile = current_profile.update_from_intent(intent_result)
            sessions[session_id].session.user_profile = updated_profile
            sessions[session_id].last_activity = datetime.now()

        logger.debug(f"Profile updated for session {session_id[:8]}...")
        logger.info(f"Updated profile: gaming_need={updated_profile.gaming_need}, camera_need={updated_profile.camera_need}, battery_need={updated_profile.battery_need}")
        return updated_profile

    def reset_profile(self, session_id: str) -> UserProfile:
        """
        重置用户需求状态，用于用户想重新开始选择。

        Args:
            session_id: 会话ID

        Returns:
            UserProfile: 新的空用户需求状态
        """
        with _sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = SessionData(session=Session(), last_activity=datetime.now())

            # 重置为空状态
            new_profile = UserProfile()
            sessions[session_id].session.user_profile = new_profile
            sessions[session_id].last_activity = datetime.now()

        logger.info(f"Profile reset for session {session_id[:8]}...")
        return new_profile
