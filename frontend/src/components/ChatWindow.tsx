import { useState } from 'react';
import type { Message, Phone, SearchHistoryItem } from '../types';
import { chatStream } from '../services/api';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { SearchHistory } from './SearchHistory';
import { useSearchHistory } from '../hooks/useSearchHistory';

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const { history, addHistory, clearHistory } = useSearchHistory();

  const handleSend = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      phones: [],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    let phones: Phone[] = [];

    try {
      for await (const event of chatStream(content)) {
        if (event.type === 'phones') {
          phones = event.data as Phone[];
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id ? { ...m, phones } : m
            )
          );
        } else if (event.type === 'content') {
          const chunk = event.data as string;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: m.content + chunk }
                : m
            )
          );
        }
      }

      // 保存搜索历史
      if (phones.length > 0) {
        addHistory(content, phones);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: `抱歉，发生了错误：${error instanceof Error ? error.message : String(error)}` }
            : m
        )
      );
    }

    setLoading(false);
  };

  // 从历史记录恢复对话
  const handleHistorySelect = (item: SearchHistoryItem) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: item.query,
      timestamp: new Date(),
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '以下是之前的推荐结果：',
      phones: item.phones,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-xl font-semibold text-gray-800">📱 手机选购助手</h1>
      </header>

      <SearchHistory
        history={history}
        onSelect={handleHistorySelect}
        onClear={clearHistory}
      />

      <MessageList messages={messages} />

      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
