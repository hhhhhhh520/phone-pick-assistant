import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchHistory } from '../components/SearchHistory';
import type { SearchHistoryItem } from '../types';

const createHistoryItem = (overrides: Partial<SearchHistoryItem> = {}): SearchHistoryItem => ({
  id: '1',
  query: '推荐一款拍照手机',
  phones: [],
  timestamp: Date.now(),
  ...overrides,
});

describe('SearchHistory', () => {
  // 空历史不渲染
  it('returns null when history is empty', () => {
    const { container } = render(
      <SearchHistory history={[]} onSelect={() => {}} onClear={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  // 渲染历史标题
  it('renders history title', () => {
    const items = [createHistoryItem()];
    render(<SearchHistory history={items} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText('搜索历史')).toBeInTheDocument();
  });

  // 渲染历史项查询文本
  it('renders history item query text', () => {
    const items = [
      createHistoryItem({ id: '1', query: '拍照手机' }),
      createHistoryItem({ id: '2', query: '游戏手机' }),
    ];
    render(<SearchHistory history={items} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText(/拍照手机/)).toBeInTheDocument();
    expect(screen.getByText(/游戏手机/)).toBeInTheDocument();
  });

  // 清空按钮渲染
  it('renders clear button', () => {
    const items = [createHistoryItem()];
    render(<SearchHistory history={items} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText('清空')).toBeInTheDocument();
  });

  // 点击清空按钮触发 onClear
  it('calls onClear when clear button is clicked', () => {
    const onClear = vi.fn();
    const items = [createHistoryItem()];
    render(<SearchHistory history={items} onSelect={() => {}} onClear={onClear} />);

    fireEvent.click(screen.getByText('清空'));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  // 点击历史项触发 onSelect
  it('calls onSelect when history item is clicked', () => {
    const onSelect = vi.fn();
    const item = createHistoryItem({ id: '1', query: '拍照手机' });
    render(<SearchHistory history={[item]} onSelect={onSelect} onClear={() => {}} />);

    // 点击包含查询文本的按钮
    const buttons = screen.getAllByRole('button');
    // 第一个按钮是清空，后面的才是历史项
    const historyButton = buttons.find((btn) => btn.textContent?.includes('拍照手机'));
    fireEvent.click(historyButton!);

    expect(onSelect).toHaveBeenCalledWith(item);
  });

  // 时间格式化 — 刚刚（<1分钟）
  it('shows "刚刚" for recent timestamps', () => {
    const item = createHistoryItem({ timestamp: Date.now() - 30000 }); // 30秒前
    render(<SearchHistory history={[item]} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText('刚刚')).toBeInTheDocument();
  });

  // 时间格式化 — 分钟前
  it('shows minutes ago for timestamps within an hour', () => {
    const item = createHistoryItem({ timestamp: Date.now() - 5 * 60000 }); // 5分钟前
    render(<SearchHistory history={[item]} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText('5分钟前')).toBeInTheDocument();
  });

  // 时间格式化 — 小时前
  it('shows hours ago for timestamps within a day', () => {
    const item = createHistoryItem({ timestamp: Date.now() - 3 * 3600000 }); // 3小时前
    render(<SearchHistory history={[item]} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText('3小时前')).toBeInTheDocument();
  });

  // 时间格式化 — 天前
  it('shows days ago for older timestamps', () => {
    const item = createHistoryItem({ timestamp: Date.now() - 2 * 86400000 }); // 2天前
    render(<SearchHistory history={[item]} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText('2天前')).toBeInTheDocument();
  });

  // 最多显示10个历史项
  it('shows at most 10 history items', () => {
    const items = Array.from({ length: 15 }, (_, i) =>
      createHistoryItem({ id: String(i), query: `查询${i}` })
    );
    render(<SearchHistory history={items} onSelect={() => {}} onClear={() => {}} />);

    // 应该有10个历史项按钮 + 1个清空按钮 = 11个按钮
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(11);
  });

  // 多个历史项渲染
  it('renders multiple history items', () => {
    const items = [
      createHistoryItem({ id: '1', query: '第一个查询' }),
      createHistoryItem({ id: '2', query: '第二个查询' }),
      createHistoryItem({ id: '3', query: '第三个查询' }),
    ];
    render(<SearchHistory history={items} onSelect={() => {}} onClear={() => {}} />);

    expect(screen.getByText(/第一个查询/)).toBeInTheDocument();
    expect(screen.getByText(/第二个查询/)).toBeInTheDocument();
    expect(screen.getByText(/第三个查询/)).toBeInTheDocument();
  });
});
