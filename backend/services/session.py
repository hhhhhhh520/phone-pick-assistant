"""
会话管理服务 - 内存存储
"""
import uuid
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# 会话存储：session_id -> (messages, last_activity_time)
sessions: Dict[str, Tuple[List[Dict], datetime]] = {}
# 线程锁，保护并发访问
_sessions_lock = threading.Lock()

# 每个会话最大保留消息数
MAX_MESSAGES = 20  # 10轮对话
# 会话过期时间（30分钟不活跃）
SESSION_EXPIRE_MINUTES = 30


class SessionService:
    def __init__(self):
        pass

    def _update_activity(self, session_id: str) -> None:
        """更新会话最后活动时间（内部方法，调用者需持有锁）"""
        if session_id in sessions:
            messages, _ = sessions[session_id]
            sessions[session_id] = (messages, datetime.now())

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        with _sessions_lock:
            sessions[session_id] = ([], datetime.now())
        return session_id

    def get_session(self, session_id: str) -> Optional[List[Dict]]:
        """获取会话历史"""
        with _sessions_lock:
            data = sessions.get(session_id)
            if data:
                return data[0]
            return None

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息到会话"""
        with _sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = ([], datetime.now())

            messages, _ = sessions[session_id]
            messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            # 保留最近的消息
            if len(messages) > MAX_MESSAGES:
                messages = messages[-MAX_MESSAGES:]

            sessions[session_id] = (messages, datetime.now())

    def get_messages(self, session_id: str) -> List[Dict]:
        """获取会话消息列表（用于LLM上下文）"""
        with _sessions_lock:
            data = sessions.get(session_id, ([], datetime.now()))
            messages = data[0]
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
                sid for sid, (_, last_activity) in sessions.items()
                if last_activity < expire_threshold
            ]
            for sid in expired_sessions:
                del sessions[sid]
                expired_count += 1
        return expired_count
