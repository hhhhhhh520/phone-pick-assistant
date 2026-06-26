import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageList } from '../components/MessageList';
import type { Message } from '../types';

// jsdom 没有 scrollIntoView，需要 mock
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

const createUserMessage = (id: string, content: string): Message => ({
  id,
  role: 'user',
  content,
  timestamp: new Date(),
});

const createAssistantMessage = (id: string, content: string): Message => ({
  id,
  role: 'assistant',
  content,
  timestamp: new Date(),
});

describe('MessageList', () => {
  // 空状态显示欢迎信息和建议
  it('shows welcome message when messages is empty', () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText('你好！我是手机选购助手')).toBeInTheDocument();
    expect(screen.getByText('告诉我你的需求，我来帮你推荐合适的手机')).toBeInTheDocument();
  });

  // 空状态显示示例问题
  it('shows example questions in empty state', () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText('试试问我：')).toBeInTheDocument();
    expect(screen.getByText('"推荐一款拍照好的手机"')).toBeInTheDocument();
    expect(screen.getByText('"iPhone 15和小米14哪个好"')).toBeInTheDocument();
    expect(screen.getByText('"3000元左右有什么推荐"')).toBeInTheDocument();
  });

  // 空状态显示手机 emoji
  it('shows phone emoji in empty state', () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText('📱')).toBeInTheDocument();
  });

  // 有消息时不显示空状态
  it('does not show empty state when messages exist', () => {
    const messages = [createUserMessage('1', 'Hello')];
    render(<MessageList messages={messages} />);

    expect(screen.queryByText('你好！我是手机选购助手')).not.toBeInTheDocument();
  });

  // 渲染用户消息
  it('renders user messages', () => {
    const messages = [
      createUserMessage('1', '推荐一款手机'),
      createUserMessage('2', '3000元左右'),
    ];
    render(<MessageList messages={messages} />);

    expect(screen.getByText('推荐一款手机')).toBeInTheDocument();
    expect(screen.getByText('3000元左右')).toBeInTheDocument();
  });

  // 渲染助手消息
  it('renders assistant messages', () => {
    const messages = [
      createAssistantMessage('1', '好的，我来帮你推荐'),
      createAssistantMessage('2', '以下是推荐结果'),
    ];
    render(<MessageList messages={messages} />);

    expect(screen.getByText('好的，我来帮你推荐')).toBeInTheDocument();
    expect(screen.getByText('以下是推荐结果')).toBeInTheDocument();
  });

  // 渲染混合消息
  it('renders mixed user and assistant messages', () => {
    const messages = [
      createUserMessage('1', '你好'),
      createAssistantMessage('2', '你好！有什么可以帮助你的？'),
      createUserMessage('3', '推荐手机'),
    ];
    render(<MessageList messages={messages} />);

    expect(screen.getByText('你好')).toBeInTheDocument();
    expect(screen.getByText('你好！有什么可以帮助你的？')).toBeInTheDocument();
    expect(screen.getByText('推荐手机')).toBeInTheDocument();
  });

  // 消息顺序正确
  it('renders messages in order', () => {
    const messages = [
      createUserMessage('1', '第一条'),
      createAssistantMessage('2', '第二条'),
      createUserMessage('3', '第三条'),
    ];
    render(<MessageList messages={messages} />);

    const textElements = screen.getAllByText(/第.条/);
    expect(textElements).toHaveLength(3);
    expect(textElements[0]).toHaveTextContent('第一条');
    expect(textElements[1]).toHaveTextContent('第二条');
    expect(textElements[2]).toHaveTextContent('第三条');
  });

  // 空消息数组不报错
  it('handles empty messages array without errors', () => {
    expect(() => {
      render(<MessageList messages={[]} />);
    }).not.toThrow();
  });

  // onQuickReply 传递给 MessageItem
  it('passes onQuickReply to MessageItem', () => {
    const onQuickReply = vi.fn();
    const messages: Message[] = [
      {
        id: '1',
        role: 'assistant',
        content: '你的预算是多少？',
        timestamp: new Date(),
        isQuestion: true,
        quickReplies: ['1000-2000', '2000-3000'],
      },
    ];

    render(<MessageList messages={messages} onQuickReply={onQuickReply} />);

    // MessageItem 中的 QuickReplyButtons 应该渲染
    expect(screen.getByText('1000-2000')).toBeInTheDocument();
    expect(screen.getByText('2000-3000')).toBeInTheDocument();
  });
});
