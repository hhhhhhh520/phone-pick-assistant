import { useState } from 'react';
import type { FormEvent } from 'react';

interface InputBarProps {
  onSend: (message: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
}

export function InputBar({ onSend, onCancel, disabled }: InputBarProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleCancel = () => {
    onCancel?.();
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 bg-white" aria-label="消息输入">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入你的问题..."
          disabled={disabled}
          aria-label="输入消息"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
        />
        {disabled && onCancel ? (
          <button
            type="button"
            onClick={handleCancel}
            aria-label="取消"
            className="px-6 py-2 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
          >
            取消
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            aria-label="发送"
            className="px-6 py-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            发送
          </button>
        )}
      </div>
    </form>
  );
}
