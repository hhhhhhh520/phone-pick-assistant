"""
会话管理服务 - 内存存储
"""
import uuid
from typing import Dict, List, Optional
from datetime import datetime

# 会话存储：session_id -> messages
sessions: Dict[str, List[Dict]] = {}

# 每个会话最大保留消息数
MAX_MESSAGES = 20  # 10轮对话


class SessionService:
    def __init__(self):
        pass

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
        return session_id

    def get_session(self, session_id: str) -> Optional[List[Dict]]:
        """获取会话历史"""
        return sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息到会话"""
        if session_id not in sessions:
            sessions[session_id] = []

        sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 保留最近的消息
        if len(sessions[session_id]) > MAX_MESSAGES:
            sessions[session_id] = sessions[session_id][-MAX_MESSAGES:]

    def get_messages(self, session_id: str) -> List[Dict]:
        """获取会话消息列表（用于LLM上下文）"""
        messages = sessions.get(session_id, [])
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return session_id in sessions
