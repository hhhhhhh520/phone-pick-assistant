import { useRef, useEffect } from 'react';
import type { Message } from '../types';
import { MessageItem } from './MessageItem';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  // 检查用户是否滚动到了非底部位置
  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;

    // 距离底部100px以内视为"在底部"
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    userScrolledUp.current = !isNearBottom;
  };

  useEffect(() => {
    // 只有用户在底部附近时才自动滚动
    if (!userScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto p-4"
    >
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-gray-400">
          <div className="text-6xl mb-4">📱</div>
          <p className="text-lg">你好！我是手机选购助手</p>
          <p className="text-sm mt-2">告诉我你的需求，我来帮你推荐合适的手机</p>
          <div className="mt-6 space-y-2 text-sm">
            <p className="text-gray-500">试试问我：</p>
            <p>"推荐一款拍照好的手机"</p>
            <p>"iPhone 15和小米14哪个好"</p>
            <p>"3000元左右有什么推荐"</p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((msg) => (
            <MessageItem key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} />
        </>
      )}
    </div>
  );
}
