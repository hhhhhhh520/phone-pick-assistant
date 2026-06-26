import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSearchHistory } from '../hooks/useSearchHistory';
import type { Phone } from '../types';

const STORAGE_KEY = 'phone_search_history';

const createPhone = (overrides: Partial<Phone> = {}): Phone => ({
  id: 1,
  brand: 'Apple',
  model: 'iPhone 15',
  price: 5999,
  screen: { size: 6.1, type: 'OLED', refresh: 60 },
  processor: 'A16',
  ram: 6,
  storage: 128,
  camera: { main: 48, ultra: 12, telephoto: 0, front: 12 },
  battery: 3349,
  charging: { wired: 20, wireless: 15 },
  weight: 171,
  features: [],
  pros: [],
  cons: [],
  suitable_for: [],
  ...overrides,
});

describe('useSearchHistory', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  // 初始状态为空历史
  it('initializes with empty history', () => {
    const { result } = renderHook(() => useSearchHistory());

    expect(result.current.history).toEqual([]);
  });

  // 从 localStorage 加载已有历史
  it('loads history from localStorage on mount', () => {
    const existingHistory = [
      {
        id: '1',
        query: '拍照手机',
        phones: [createPhone()],
        timestamp: Date.now(),
      },
    ];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(existingHistory));

    const { result } = renderHook(() => useSearchHistory());

    expect(result.current.history).toEqual(existingHistory);
  });

  // localStorage 数据损坏时初始化为空
  it('initializes with empty history when localStorage data is corrupted', () => {
    localStorage.setItem(STORAGE_KEY, 'invalid-json');

    const { result } = renderHook(() => useSearchHistory());

    expect(result.current.history).toEqual([]);
  });

  // 添加历史记录
  it('adds a history item', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      result.current.addHistory('拍照手机', [createPhone()]);
    });

    expect(result.current.history).toHaveLength(1);
    expect(result.current.history[0].query).toBe('拍照手机');
    expect(result.current.history[0].phones).toHaveLength(1);
  });

  // 添加后持久化到 localStorage
  it('persists history to localStorage after adding', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      result.current.addHistory('拍照手机', []);
    });

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
    expect(stored).toHaveLength(1);
    expect(stored[0].query).toBe('拍照手机');
  });

  // 添加的项目排在最前面
  it('adds new items to the beginning of history', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      result.current.addHistory('第一个', []);
    });
    act(() => {
      result.current.addHistory('第二个', []);
    });

    expect(result.current.history[0].query).toBe('第二个');
    expect(result.current.history[1].query).toBe('第一个');
  });

  // 重复查询不重复添加
  it('does not duplicate queries', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      result.current.addHistory('拍照手机', []);
    });
    act(() => {
      result.current.addHistory('拍照手机', [createPhone()]);
    });

    expect(result.current.history).toHaveLength(1);
    expect(result.current.history[0].phones).toHaveLength(1);
  });

  // 最多保留20条历史
  it('limits history to 20 items', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      for (let i = 0; i < 25; i++) {
        result.current.addHistory(`查询${i}`, []);
      }
    });

    expect(result.current.history).toHaveLength(20);
    // 最新的在前
    expect(result.current.history[0].query).toBe('查询24');
    expect(result.current.history[19].query).toBe('查询5');
  });

  // 清空历史
  it('clears all history', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      result.current.addHistory('拍照手机', []);
    });
    act(() => {
      result.current.clearHistory();
    });

    expect(result.current.history).toEqual([]);
  });

  // 清空后 localStorage 也被清除
  it('removes from localStorage after clearing', () => {
    const { result } = renderHook(() => useSearchHistory());

    act(() => {
      result.current.addHistory('拍照手机', []);
    });
    act(() => {
      result.current.clearHistory();
    });

    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  // 添加历史项有正确的 id 和 timestamp
  it('generates unique id and timestamp for each item', () => {
    const { result } = renderHook(() => useSearchHistory());

    const before = Date.now();
    act(() => {
      result.current.addHistory('查询1', []);
    });
    const after = Date.now();

    const item = result.current.history[0];
    expect(item.id).toBeTruthy();
    expect(item.timestamp).toBeGreaterThanOrEqual(before);
    expect(item.timestamp).toBeLessThanOrEqual(after);
  });
});
