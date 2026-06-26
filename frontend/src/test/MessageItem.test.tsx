import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MessageItem } from '../components/MessageItem';
import type { Message } from '../types';

describe('MessageItem', () => {
  // 基础用户消息测试
  it('renders user message with correct styling', () => {
    const message: Message = {
      id: '1',
      role: 'user',
      content: 'Hello, I want a phone',
      timestamp: new Date(),
    };

    render(<MessageItem message={message} />);

    expect(screen.getByText('Hello, I want a phone')).toBeInTheDocument();
    // 用户消息应该右对齐
    const container = screen.getByText('Hello, I want a phone').closest('div');
    expect(container?.parentElement).toHaveClass('justify-end');
  });

  // 基础助手消息测试
  it('renders assistant message with correct styling', () => {
    const message: Message = {
      id: '2',
      role: 'assistant',
      content: 'I can help you find a phone',
      timestamp: new Date(),
    };

    render(<MessageItem message={message} />);

    expect(screen.getByText('I can help you find a phone')).toBeInTheDocument();
    // 助手消息应该左对齐
    const container = screen.getByText('I can help you find a phone').closest('div');
    expect(container?.parentElement).toHaveClass('justify-start');
  });

  // 追问消息样式测试 - 浅蓝色背景
  it('renders question message with light blue background', () => {
    const message: Message = {
      id: '3',
      role: 'assistant',
      content: 'What is your budget?',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies: ['1000-2000', '2000-3000', '3000+'],
    };

    render(<MessageItem message={message} />);

    const textElement = screen.getByText('What is your budget?');
    const container = textElement.closest('div');

    // 追问消息应该有浅蓝色背景
    expect(container).toHaveClass('bg-blue-50');
    // 应该有蓝色边框
    expect(container).toHaveClass('border-blue-200');
    // 应该有蓝色文字
    expect(container).toHaveClass('text-gray-800');
  });

  // 快捷回复按钮渲染测试
  it('renders quick reply buttons for question message', () => {
    const quickReplies = ['1000-2000', '2000-3000', '3000+'];
    const message: Message = {
      id: '4',
      role: 'assistant',
      content: 'What is your budget?',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies,
    };

    render(<MessageItem message={message} />);

    // 所有快捷回复按钮应该渲染
    quickReplies.forEach((reply) => {
      expect(screen.getByText(reply)).toBeInTheDocument();
    });
  });

  // 快捷回复按钮不渲染测试 - 非追问消息
  it('does not render quick reply buttons for non-question message', () => {
    const message: Message = {
      id: '5',
      role: 'assistant',
      content: 'Here are some recommendations',
      timestamp: new Date(),
      quickReplies: ['Option A', 'Option B'], // 即使有 quickReplies
    };

    render(<MessageItem message={message} />);

    expect(screen.queryByText('Option A')).not.toBeInTheDocument();
    expect(screen.queryByText('Option B')).not.toBeInTheDocument();
  });

  // 快捷回复按钮不渲染测试 - 空 quickReplies
  it('does not render quick reply buttons when quickReplies is empty', () => {
    const message: Message = {
      id: '6',
      role: 'assistant',
      content: 'What is your budget?',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies: [],
    };

    render(<MessageItem message={message} />);

    // 不应该有按钮元素
    const buttons = screen.queryAllByRole('button');
    expect(buttons).toHaveLength(0);
  });

  // 点击快捷回复触发回调测试
  it('calls onQuickReply callback when quick reply button is clicked', () => {
    const onQuickReply = vi.fn();
    const message: Message = {
      id: '7',
      role: 'assistant',
      content: 'What is your budget?',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies: ['1000-2000', '2000-3000'],
    };

    render(<MessageItem message={message} onQuickReply={onQuickReply} />);

    // 点击第一个快捷回复
    fireEvent.click(screen.getByText('1000-2000'));

    expect(onQuickReply).toHaveBeenCalledTimes(1);
    expect(onQuickReply).toHaveBeenCalledWith('1000-2000');
  });

  // 多次点击不同快捷回复测试
  it('handles multiple quick reply clicks', () => {
    const onQuickReply = vi.fn();
    const message: Message = {
      id: '8',
      role: 'assistant',
      content: 'Select your preference',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies: ['Budget', 'Performance', 'Camera'],
    };

    render(<MessageItem message={message} onQuickReply={onQuickReply} />);

    // 点击多个快捷回复
    fireEvent.click(screen.getByText('Budget'));
    fireEvent.click(screen.getByText('Camera'));

    expect(onQuickReply).toHaveBeenCalledTimes(2);
    expect(onQuickReply).toHaveBeenNthCalledWith(1, 'Budget');
    expect(onQuickReply).toHaveBeenNthCalledWith(2, 'Camera');
  });

  // 无 onQuickReply 时不报错
  it('does not throw when clicking quick reply without onQuickReply callback', () => {
    const message: Message = {
      id: '9',
      role: 'assistant',
      content: 'What is your budget?',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies: ['1000-2000'],
    };

    render(<MessageItem message={message} />);

    // 点击不应报错
    expect(() => {
      fireEvent.click(screen.getByText('1000-2000'));
    }).not.toThrow();
  });

  // 对比消息样式测试
  it('renders compare message with phones', () => {
    const message: Message = {
      id: '10',
      role: 'assistant',
      content: 'Here is a comparison',
      timestamp: new Date(),
      isCompare: true,
      phones: [
        {
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
        },
        {
          id: 2,
          brand: 'Samsung',
          model: 'Galaxy S24',
          price: 5499,
          screen: { size: 6.2, type: 'AMOLED', refresh: 120 },
          processor: 'Exynos 2400',
          ram: 8,
          storage: 256,
          camera: { main: 50, ultra: 12, telephoto: 10, front: 12 },
          battery: 4000,
          charging: { wired: 25, wireless: 15 },
          weight: 167,
          features: [],
          pros: [],
          cons: [],
          suitable_for: [],
        },
      ],
    };

    render(<MessageItem message={message} />);

    expect(screen.getByText('Here is a comparison')).toBeInTheDocument();
    // 对比表格会显示品牌和型号
    expect(screen.getByText('iPhone 15')).toBeInTheDocument();
    expect(screen.getByText('Galaxy S24')).toBeInTheDocument();
  });

  // 普通推荐消息样式
  it('renders recommendation message with phone cards', () => {
    const message: Message = {
      id: '11',
      role: 'assistant',
      content: 'I recommend these phones',
      timestamp: new Date(),
      isCompare: false,
      phones: [
        {
          id: 2,
          brand: 'Xiaomi',
          model: 'Redmi Note 13',
          price: 1299,
          screen: { size: 6.67, type: 'OLED', refresh: 120 },
          processor: 'Snapdragon 7s Gen 2',
          ram: 8,
          storage: 256,
          camera: { main: 200, ultra: 8, telephoto: 2, front: 16 },
          battery: 5100,
          charging: { wired: 33, wireless: 0 },
          weight: 188,
          features: ['快充'],
          pros: ['性价比高'],
          cons: ['塑料机身'],
          suitable_for: ['学生'],
        },
      ],
    };

    render(<MessageItem message={message} />);

    expect(screen.getByText('I recommend these phones')).toBeInTheDocument();
    // PhoneCard 显示品牌和型号分开
    expect(screen.getByText('Xiaomi')).toBeInTheDocument();
    expect(screen.getByText('Redmi Note 13')).toBeInTheDocument();
  });

  // 追问消息与普通助手消息样式对比
  it('question message has different styling from regular assistant message', () => {
    const regularMessage: Message = {
      id: '12',
      role: 'assistant',
      content: 'Regular response',
      timestamp: new Date(),
    };

    const questionMessage: Message = {
      id: '13',
      role: 'assistant',
      content: 'Question response',
      timestamp: new Date(),
      isQuestion: true,
      quickReplies: ['Yes', 'No'],
    };

    const { rerender } = render(<MessageItem message={regularMessage} />);
    const regularContainer = screen.getByText('Regular response').closest('div');

    // 普通助手消息应该有白色背景
    expect(regularContainer).toHaveClass('bg-white');

    rerender(<MessageItem message={questionMessage} />);
    const questionContainer = screen.getByText('Question response').closest('div');

    // 追问消息应该有浅蓝色背景
    expect(questionContainer).toHaveClass('bg-blue-50');
    expect(questionContainer).toHaveClass('border-blue-200');
  });
});