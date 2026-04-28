import { useState, useEffect, useCallback } from 'react';
import type { Phone, SearchHistoryItem } from '../types';

const STORAGE_KEY = 'phone_search_history';
const MAX_HISTORY = 20;

export function useSearchHistory() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);

  // 从localStorage加载历史
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch {
        setHistory([]);
      }
    }
  }, []);

  // 添加历史记录
  const addHistory = useCallback((query: string, phones: Phone[]) => {
    const newItem: SearchHistoryItem = {
      id: Date.now().toString(),
      query,
      phones,
      timestamp: Date.now(),
    };

    setHistory((prev) => {
      const filtered = prev.filter((item) => item.query !== query);
      const updated = [newItem, ...filtered].slice(0, MAX_HISTORY);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  // 清空历史
  const clearHistory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setHistory([]);
  }, []);

  return {
    history,
    addHistory,
    clearHistory,
  };
}
