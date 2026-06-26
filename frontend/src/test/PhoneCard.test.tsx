import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PhoneCard } from '../components/PhoneCard';
import type { Phone } from '../types';

// 创建测试用的手机数据
const createPhone = (overrides: Partial<Phone> = {}): Phone => ({
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
  features: ['Face ID', 'MagSafe', '灵动岛', '防水'],
  pros: [],
  cons: [],
  suitable_for: [],
  ...overrides,
});

describe('PhoneCard', () => {
  // 渲染手机基本信息
  it('renders phone brand and model', () => {
    const phone = createPhone();
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('iPhone 15')).toBeInTheDocument();
  });

  // 渲染价格
  it('renders phone price with yen symbol', () => {
    const phone = createPhone({ price: 5999 });
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText('¥5999')).toBeInTheDocument();
  });

  // 渲染处理器信息
  it('renders processor info', () => {
    const phone = createPhone({ processor: 'Snapdragon 8 Gen 3' });
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText(/Snapdragon 8 Gen 3/)).toBeInTheDocument();
  });

  // 渲染内存和存储信息
  it('renders RAM and storage info', () => {
    const phone = createPhone({ ram: 12, storage: 256 });
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText('12GB')).toBeInTheDocument();
    expect(screen.getByText('256GB')).toBeInTheDocument();
  });

  // 渲染电池信息
  it('renders battery info', () => {
    const phone = createPhone({ battery: 5000 });
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText('5000mAh')).toBeInTheDocument();
  });

  // 处理缺失字段显示默认值
  it('shows dash for missing optional fields', () => {
    const phone = createPhone({ processor: '', ram: 0, storage: 0, battery: 0 });
    render(<PhoneCard phone={phone} />);

    // processor 为空字符串时显示 '-'
    const dashes = screen.getAllByText('-');
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  // 特性标签显示（最多3个）
  it('shows up to 3 feature tags', () => {
    const phone = createPhone({
      features: ['Face ID', 'MagSafe', '灵动岛', '防水', '5G'],
    });
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText('Face ID')).toBeInTheDocument();
    expect(screen.getByText('MagSafe')).toBeInTheDocument();
    expect(screen.getByText('灵动岛')).toBeInTheDocument();
    // 第4个和第5个不应该显示
    expect(screen.queryByText('防水')).not.toBeInTheDocument();
    expect(screen.queryByText('5G')).not.toBeInTheDocument();
  });

  // 空特性列表不显示标签区域
  it('does not render feature tags when features is empty', () => {
    const phone = createPhone({ features: [] });
    const { container } = render(<PhoneCard phone={phone} />);

    // 不应该有 feature tags 的容器
    const featureContainer = container.querySelector('.flex.flex-wrap.gap-1');
    expect(featureContainer).toBeNull();
  });

  // 图片加载失败时显示默认图标
  it('shows default phone icon when image fails to load', () => {
    const phone = createPhone({ imageUrl: 'https://example.com/broken.jpg' });
    render(<PhoneCard phone={phone} />);

    // 初始渲染 img
    const img = document.querySelector('img');
    expect(img).toBeInTheDocument();

    // 模拟图片加载失败
    fireEvent.error(img!);

    // 失败后应显示默认 SVG 图标
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
    // img 应该消失
    expect(document.querySelector('img')).not.toBeInTheDocument();
  });

  // 没有 imageUrl 时显示默认图标
  it('shows default phone icon when no imageUrl', () => {
    const phone = createPhone({ imageUrl: undefined });
    render(<PhoneCard phone={phone} />);

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  // 本地图片路径拼接 API 地址
  it('constructs full image URL for local paths', () => {
    const phone = createPhone({ imageUrl: '/images/iphone15.jpg' });
    render(<PhoneCard phone={phone} />);

    const img = document.querySelector('img');
    expect(img).toHaveAttribute('src', expect.stringContaining('/images/iphone15.jpg'));
  });

  // 外部 URL 直接使用
  it('uses external URL directly', () => {
    const phone = createPhone({ imageUrl: 'https://example.com/phone.jpg' });
    render(<PhoneCard phone={phone} />);

    const img = document.querySelector('img');
    expect(img).toHaveAttribute('src', 'https://example.com/phone.jpg');
  });

  // 点击卡片触发 onClick 回调
  it('calls onClick when card is clicked', () => {
    const onClick = vi.fn();
    const phone = createPhone();
    render(<PhoneCard phone={phone} onClick={onClick} />);

    // 点击卡片容器
    const card = screen.getByText('iPhone 15').closest('div')?.parentElement?.parentElement;
    fireEvent.click(card!);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  // 无 onClick 时不报错
  it('does not throw when clicked without onClick callback', () => {
    const phone = createPhone();
    render(<PhoneCard phone={phone} />);

    const card = screen.getByText('iPhone 15').closest('div')?.parentElement?.parentElement;
    expect(() => {
      fireEvent.click(card!);
    }).not.toThrow();
  });

  // 影像评分卡片渲染
  it('renders camera scoring card when cameraScoring is provided', () => {
    const phone = createPhone({
      cameraScoring: {
        total: 92,
        chip_score: 90,
        hardware_score: 95,
        algorithm_score: 88,
        grade: '旗舰',
      },
    });
    render(<PhoneCard phone={phone} />);

    expect(screen.getByText('影像评分')).toBeInTheDocument();
    expect(screen.getByText('旗舰')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument();
    expect(screen.getByText('芯片')).toBeInTheDocument();
    expect(screen.getByText('硬件')).toBeInTheDocument();
    expect(screen.getByText('算法')).toBeInTheDocument();
  });

  // 无影像评分时不渲染评分卡片
  it('does not render camera scoring card when cameraScoring is not provided', () => {
    const phone = createPhone({ cameraScoring: undefined });
    render(<PhoneCard phone={phone} />);

    expect(screen.queryByText('影像评分')).not.toBeInTheDocument();
  });
});
