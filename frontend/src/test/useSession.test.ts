import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSession } from '../hooks/useSession';

const SESSION_KEY = 'phone_picker_session';

describe('useSession', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  // 初始状态 sessionId 为 null
  it('initializes with null sessionId', () => {
    const { result } = renderHook(() => useSession());

    expect(result.current.sessionId).toBeNull();
  });

  // 从 localStorage 加载已有 session
  it('loads session from localStorage on mount', () => {
    localStorage.setItem(SESSION_KEY, 'existing-session-123');

    const { result } = renderHook(() => useSession());

    expect(result.current.sessionId).toBe('existing-session-123');
  });

  // 保存 session 到 localStorage
  it('saves session to localStorage', () => {
    const { result } = renderHook(() => useSession());

    act(() => {
      result.current.saveSession('new-session-456');
    });

    expect(result.current.sessionId).toBe('new-session-456');
    expect(localStorage.getItem(SESSION_KEY)).toBe('new-session-456');
  });

  // 保存后更新 sessionId 状态
  it('updates sessionId state after saving', () => {
    const { result } = renderHook(() => useSession());

    expect(result.current.sessionId).toBeNull();

    act(() => {
      result.current.saveSession('session-abc');
    });

    expect(result.current.sessionId).toBe('session-abc');
  });

  // 清除 session
  it('clears session from localStorage', () => {
    const { result } = renderHook(() => useSession());

    act(() => {
      result.current.saveSession('session-to-clear');
    });
    act(() => {
      result.current.clearSession();
    });

    expect(localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  // 清除后 sessionId 变为 null
  it('sets sessionId to null after clearing', () => {
    const { result } = renderHook(() => useSession());

    act(() => {
      result.current.saveSession('session-xyz');
    });
    expect(result.current.sessionId).toBe('session-xyz');

    act(() => {
      result.current.clearSession();
    });

    expect(result.current.sessionId).toBeNull();
  });

  // 保存并清除的完整流程
  it('handles full save and clear lifecycle', () => {
    const { result } = renderHook(() => useSession());

    // 初始为空
    expect(result.current.sessionId).toBeNull();

    // 保存
    act(() => {
      result.current.saveSession('lifecycle-session');
    });
    expect(result.current.sessionId).toBe('lifecycle-session');
    expect(localStorage.getItem(SESSION_KEY)).toBe('lifecycle-session');

    // 清除
    act(() => {
      result.current.clearSession();
    });
    expect(result.current.sessionId).toBeNull();
    expect(localStorage.getItem(SESSION_KEY)).toBeNull();
  });

  // 覆盖已有 session
  it('overwrites existing session when saving new one', () => {
    localStorage.setItem(SESSION_KEY, 'old-session');

    const { result } = renderHook(() => useSession());

    // 加载旧 session
    expect(result.current.sessionId).toBe('old-session');

    // 保存新 session
    act(() => {
      result.current.saveSession('new-session');
    });

    expect(result.current.sessionId).toBe('new-session');
    expect(localStorage.getItem(SESSION_KEY)).toBe('new-session');
  });
});
