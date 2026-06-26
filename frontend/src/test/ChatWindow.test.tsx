import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatWindow } from '../components/ChatWindow';
import * as api from '../services/api';

// Mock scrollIntoView for jsdom
Element.prototype.scrollIntoView = vi.fn();

// Mock API
vi.mock('../services/api', () => ({
  chatStream: vi.fn(),
  abortCurrentRequest: vi.fn(),
}));

// Mock hooks
vi.mock('../hooks/useSearchHistory', () => ({
  useSearchHistory: () => ({
    history: [],
    addHistory: vi.fn(),
    clearHistory: vi.fn(),
  }),
}));

vi.mock('../hooks/useSession', () => ({
  useSession: () => ({
    sessionId: 'test-session-id',
    saveSession: vi.fn(),
  }),
}));

describe('ChatWindow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 基础渲染测试
  it('renders chat window with header and input', () => {
    render(<ChatWindow />);

    // 标题包含 emoji，使用 getAllByText 或更精确的选择器
    const heading = screen.getByRole('heading', { name: /手机选购助手/ });
    expect(heading).toBeInTheDocument();
    expect(screen.getByPlaceholderText('输入你的问题...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '发送' })).toBeInTheDocument();
  });

  // 发送消息测试
  it('sends message when clicking send button', async () => {
    const mockStream = vi.fn().mockImplementation(async function* () {
      yield { type: 'session', data: 'new-session-id' };
      yield { type: 'intent', data: 'recommend' };
      yield { type: 'content', data: '好的' };
      yield { type: 'content', data: '，我来为您推荐' };
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    const sendButton = screen.getByRole('button', { name: '发送' });

    // 输入消息
    fireEvent.change(input, { target: { value: '我要买手机' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.chatStream).toHaveBeenCalledWith('我要买手机', 'test-session-id');
    });

    // 用户消息应该显示
    await waitFor(() => {
      expect(screen.getByText('我要买手机')).toBeInTheDocument();
    });
  });

  // 接收 question 事件测试
  it('handles question event and displays quick replies', async () => {
    const mockStream = vi.fn().mockImplementation(async function* () {
      yield { type: 'question', data: { question: '您的预算是多少？', quick_replies: ['1000-2000元', '2000-3000元', '3000元以上'], missing_fields: ['budget'] } };
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '推荐手机' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      // 追问消息应该显示
      expect(screen.getByText('您的预算是多少？')).toBeInTheDocument();
      // 快捷回复按钮应该显示
      expect(screen.getByText('1000-2000元')).toBeInTheDocument();
      expect(screen.getByText('2000-3000元')).toBeInTheDocument();
      expect(screen.getByText('3000元以上')).toBeInTheDocument();
    });
  });

  // question 事件设置 isQuestion 和 quickReplies
  it('sets isQuestion and quickReplies from question event', async () => {
    const mockStream = vi.fn().mockImplementation(async function* () {
      yield { type: 'question', data: { question: '您偏好哪个品牌？', quick_replies: ['华为', '小米', '苹果'], missing_fields: ['brand'] } };
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '帮我选手机' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      // 验证追问消息渲染了快捷回复
      const quickReplyButtons = screen.getAllByRole('button').filter(
        (btn) => ['华为', '小米', '苹果'].some((text) => btn.textContent?.includes(text))
      );
      expect(quickReplyButtons).toHaveLength(3);
    });
  });

  // handleQuickReply 发送消息测试
  it('sends message when quick reply is clicked', async () => {
    // 第一次调用返回追问
    const mockStream1 = vi.fn().mockImplementation(async function* () {
      yield { type: 'question', data: { question: '您的预算？', quick_replies: ['1000-2000元'], missing_fields: ['budget'] } };
    });

    // 第二次调用返回推荐结果
    const mockStream2 = vi.fn().mockImplementation(async function* () {
      yield { type: 'intent', data: 'recommend' };
      yield { type: 'phones', data: [] };
      yield { type: 'content', data: '已收到您的预算' };
    });

    vi.mocked(api.chatStream)
      .mockImplementationOnce(mockStream1)
      .mockImplementationOnce(mockStream2);

    render(<ChatWindow />);

    // 发送初始消息
    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '推荐手机' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    // 等待追问消息出现
    await waitFor(() => {
      expect(screen.getByText('您的预算？')).toBeInTheDocument();
    });

    // 点击快捷回复
    fireEvent.click(screen.getByText('1000-2000元'));

    // 应该发送快捷回复内容
    await waitFor(() => {
      expect(api.chatStream).toHaveBeenCalledTimes(2);
      expect(api.chatStream).toHaveBeenNthCalledWith(2, '1000-2000元', 'test-session-id');
    });
  });

  // 取消请求测试
  it('cancels request when clicking cancel button', async () => {
    // 创建一个不会立即完成的 stream
    const mockStream = vi.fn().mockImplementation(async function* () {
      yield { type: 'content', data: '正在思考...' };
      // 模拟长时间等待
      await new Promise((resolve) => setTimeout(resolve, 10000));
      yield { type: 'content', data: '结果' };
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    // 发送消息
    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '推荐' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    // 等待取消按钮出现
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    });

    // 点击取消
    fireEvent.click(screen.getByRole('button', { name: '取消' }));

    // 应该调用 abortCurrentRequest
    expect(api.abortCurrentRequest).toHaveBeenCalled();
  });

  // phones 事件处理测试
  it('handles phones event and displays phone cards', async () => {
    const mockPhones = [
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
    ];

    const mockStream = vi.fn().mockImplementation(async function* () {
      yield { type: 'intent', data: 'recommend' };
      yield { type: 'phones', data: mockPhones };
      yield { type: 'content', data: '我为您推荐这款手机' };
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '推荐苹果手机' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      // 手机卡片应该显示品牌和型号
      expect(screen.getByText('Apple')).toBeInTheDocument();
      expect(screen.getByText('iPhone 15')).toBeInTheDocument();
    });
  });

  // compare 意图处理测试
  it('handles compare intent and displays compare table', async () => {
    const mockPhones = [
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
    ];

    const mockStream = vi.fn().mockImplementation(async function* () {
      yield { type: 'intent', data: 'compare' };
      yield { type: 'phones', data: mockPhones };
      yield { type: 'content', data: '这是两款手机的对比' };
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '对比 iPhone 15 和 Galaxy S24' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      // 对比表格应该显示两款手机（品牌和型号分开显示）
      expect(screen.getByText('iPhone 15')).toBeInTheDocument();
      expect(screen.getByText('Galaxy S24')).toBeInTheDocument();
    });
  });

  // 错误处理测试
  it('handles error gracefully', async () => {
    const mockStream = vi.fn().mockImplementation(async function* () {
      throw new Error('Network error');
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '测试错误' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText(/抱歉，发生了错误/)).toBeInTheDocument();
    });
  });

  // AbortError 处理测试
  it('handles AbortError with cancellation message', async () => {
    const abortError = new Error('Aborted');
    abortError.name = 'AbortError';

    const mockStream = vi.fn().mockImplementation(async function* () {
      throw abortError;
    });

    vi.mocked(api.chatStream).mockImplementation(mockStream);

    render(<ChatWindow />);

    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '测试取消' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText('请求已取消')).toBeInTheDocument();
    });
  });

  // 连续追问测试
  it('handles multiple consecutive questions', async () => {
    // 第一次追问
    const mockStream1 = vi.fn().mockImplementation(async function* () {
      yield { type: 'question', data: { question: '您的预算？', quick_replies: ['1000-2000'], missing_fields: ['budget'] } };
    });

    // 第二次追问（点击快捷回复后）
    const mockStream2 = vi.fn().mockImplementation(async function* () {
      yield { type: 'question', data: { question: '您偏好什么品牌？', quick_replies: ['华为', '小米'], missing_fields: ['brand'] } };
    });

    vi.mocked(api.chatStream)
      .mockImplementationOnce(mockStream1)
      .mockImplementationOnce(mockStream2);

    render(<ChatWindow />);

    // 发送初始消息
    const input = screen.getByPlaceholderText('输入你的问题...');
    fireEvent.change(input, { target: { value: '推荐手机' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));

    await waitFor(() => {
      expect(screen.getByText('您的预算？')).toBeInTheDocument();
    });

    // 点击快捷回复触发第二次追问
    fireEvent.click(screen.getByText('1000-2000'));

    await waitFor(() => {
      expect(screen.getByText('您偏好什么品牌？')).toBeInTheDocument();
      expect(screen.getByText('华为')).toBeInTheDocument();
      expect(screen.getByText('小米')).toBeInTheDocument();
    });
  });
});