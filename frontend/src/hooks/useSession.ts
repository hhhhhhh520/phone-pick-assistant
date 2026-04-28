import { useState, useEffect, useCallback } from 'react';

const SESSION_KEY = 'phone_picker_session';

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  // 从localStorage加载session_id
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      setSessionId(stored);
    }
  }, []);

  // 保存session_id
  const saveSession = useCallback((id: string) => {
    localStorage.setItem(SESSION_KEY, id);
    setSessionId(id);
  }, []);

  // 清除session
  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    setSessionId(null);
  }, []);

  return {
    sessionId,
    saveSession,
    clearSession,
  };
}
