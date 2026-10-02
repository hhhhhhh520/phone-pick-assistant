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

// ISSUE-049：内部 pain_point_type code 不得泄漏到用户可见标题
describe('痛点追问标题 code 防泄漏 (ISSUE-049)', () => {
  const painMsg = (painPointType: string): Message => ({
    id: `pp-${painPointType}`,
    role: 'assistant',
    content: '您确定要看看其他选择吗？',
    timestamp: new Date(),
    isQuestion: true,
    quickReplies: ['接受', '换品牌'],
    painPointType,
  });

  // 后端 question.py PAIN_POINT_TEMPLATES 全集（6 个 code）
  const BACKEND_CODES = [
    'budget_too_low_for_features',
    'brand_budget_conflict',
    'gaming_camera_budget_conflict',
    'battery_vs_gaming',
    'high_demand_low_budget_general',
    'brand_not_match_features',
  ];

  it('brand_not_match_features 显示中文标签，DOM 不含原始 code', () => {
    render(<MessageItem message={painMsg('brand_not_match_features')} />);
    expect(screen.getByText('关于品牌与功能的追问')).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('brand_not_match_features');
  });

  // 标签表须与后端 question.py PAIN_POINT_TEMPLATES 一一对应。
  // 注意：本列表是前端手抄副本（测试无法 import Python），后端加键时需同步 typeNames 与此处
  const EXPECTED_LABELS: Record<string, string> = {
    budget_too_low_for_features: '预算不足',
    brand_budget_conflict: '品牌与预算',
    gaming_camera_budget_conflict: '游戏与拍照',
    battery_vs_gaming: '续航与游戏',
    high_demand_low_budget_general: '需求与预算',
    brand_not_match_features: '品牌与功能'
  };

  it('后端全部 6 个 code 均映射到专属中文标签，DOM 不含任何原始 code', () => {
    for (const code of BACKEND_CODES) {
      const { unmount } = render(<MessageItem message={painMsg(code)} />);
      expect(screen.getByText(`关于${EXPECTED_LABELS[code]}的追问`)).toBeInTheDocument();
      // 兜底文案不得成为"映射缺失但测试仍绿"的替身
      expect(screen.queryByText('关于偏好确认的追问')).not.toBeInTheDocument();
      expect(document.body.textContent).not.toContain(code);
      unmount();
    }
  });

  it('未知的新 code 兜底为通用文案，不泄漏原始 code', () => {
    render(<MessageItem message={painMsg('future_new_type_xyz')} />);
    expect(screen.getByText('关于偏好确认的追问')).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('future_new_type_xyz');
  });

  it('旧语义键 battery 仍映射"续航问题"（回归）', () => {
    render(<MessageItem message={painMsg('battery')} />);
    expect(screen.getByText('关于续航问题的追问')).toBeInTheDocument();
  });
});

// ISSUE-049：severity 枚举后端实际发出 high/medium/low，徽标必须渲染（原 mild/moderate/severe 与后端零交集，徽标从未显示过）
describe('痛点严重度徽标 severity 枚举对齐 (ISSUE-049)', () => {
  const painMsg = (severity?: string): Message => ({
    id: 'pp-sev',
    role: 'assistant',
    content: '您确定要看看其他选择吗？',
    timestamp: new Date(),
    isQuestion: true,
    quickReplies: ['接受', '换品牌'],
    painPointType: 'brand_not_match_features',
    painPointSeverity: severity,
  });

  it('severity=high/medium/low 渲染对应徽标文案（后端实际枚举）', () => {
    const cases: Record<string, string> = {
      high: '重点关注',
      medium: '中度关注',
      low: '轻度关注',
    };
    for (const [sev, label] of Object.entries(cases)) {
      const { unmount } = render(<MessageItem message={painMsg(sev)} />);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    }
  });

  it('旧键 mild 仍渲染"轻度关注"（回归）', () => {
    render(<MessageItem message={painMsg('mild')} />);
    expect(screen.getByText('轻度关注')).toBeInTheDocument();
  });

  it('severity 缺失时不渲染徽标', () => {
    render(<MessageItem message={painMsg(undefined)} />);
    expect(screen.queryByText(/(轻度|中度|重点)关注/)).not.toBeInTheDocument();
  });
});
