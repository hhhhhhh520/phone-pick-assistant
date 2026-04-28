import { useState } from 'react';
import type { Message, Phone } from '../types';
import { chatStream } from '../services/api';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

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

    try {
      for await (const event of chatStream(content)) {
        if (event.type === 'phones') {
          const phones = event.data as Phone[];
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
    } catch (error) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: '抱歉，发生了错误，请稍后再试。' }
            : m
        )
      );
    }

    setLoading(false);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-xl font-semibold text-gray-800">📱 手机选购助手</h1>
      </header>

      <MessageList messages={messages} />

      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}