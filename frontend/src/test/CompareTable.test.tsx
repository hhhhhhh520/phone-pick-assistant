import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CompareTable } from '../components/CompareTable';
import type { Phone } from '../types';

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
  features: [],
  pros: [],
  cons: [],
  suitable_for: [],
  ...overrides,
});

describe('CompareTable', () => {
  const phone1 = createPhone({
    id: 1,
    brand: 'Apple',
    model: 'iPhone 15',
    price: 5999,
    processor: 'A16',
    ram: 6,
    storage: 128,
    battery: 3349,
    weight: 171,
    camera: { main: 48, ultra: 12, telephoto: 0, front: 12 },
    charging: { wired: 20, wireless: 15 },
    screen: { size: 6.1, type: 'OLED', refresh: 60 },
  });

  const phone2 = createPhone({
    id: 2,
    brand: 'Samsung',
    model: 'Galaxy S24',
    price: 5499,
    processor: 'Exynos 2400',
    ram: 8,
    storage: 256,
    battery: 4000,
    weight: 167,
    camera: { main: 50, ultra: 12, telephoto: 10, front: 12 },
    charging: { wired: 25, wireless: 15 },
    screen: { size: 6.2, type: 'AMOLED', refresh: 120 },
  });

  // 不足2部手机不渲染
  it('returns null when less than 2 phones', () => {
    const { container } = render(<CompareTable phones={[phone1]} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when phones array is empty', () => {
    const { container } = render(<CompareTable phones={[]} />);
    expect(container.firstChild).toBeNull();
  });

  // 渲染表格
  it('renders comparison table with both phone headers', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('Apple iPhone 15')).toBeInTheDocument();
    expect(screen.getByText('Samsung Galaxy S24')).toBeInTheDocument();
  });

  // 渲染所有参数行
  it('renders all parameter rows', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    const labels = [
      '品牌', '型号', '价格', '处理器', '内存', '存储',
      '屏幕', '电池', '主摄', '快充', '重量',
    ];
    labels.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  // 渲染品牌和型号值
  it('renders brand and model values', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('iPhone 15')).toBeInTheDocument();
    expect(screen.getByText('Samsung')).toBeInTheDocument();
    expect(screen.getByText('Galaxy S24')).toBeInTheDocument();
  });

  // 差异高亮 — 不同的参数应该有黄色背景
  it('highlights rows with different values in yellow', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    // 价格不同 (5999 vs 5499) — 应该高亮
    const priceRow = screen.getByText('¥5,999').closest('tr');
    expect(priceRow).toHaveClass('bg-yellow-50');

    // 处理器不同 — 应该高亮
    const processorRow = screen.getByText('A16').closest('tr');
    expect(processorRow).toHaveClass('bg-yellow-50');
  });

  // 相同参数不高亮
  it('does not highlight rows with same values', () => {
    const samePhone1 = createPhone({ id: 1 });
    const samePhone2 = createPhone({ id: 2, model: 'iPhone 15 Pro' });

    render(<CompareTable phones={[samePhone1, samePhone2]} />);

    // 品牌相同 — 不应该高亮（两个 Apple 单元格）
    const brandCells = screen.getAllByText('Apple');
    expect(brandCells.length).toBe(2);
    brandCells.forEach((cell) => {
      const row = cell.closest('tr');
      expect(row).not.toHaveClass('bg-yellow-50');
    });
  });

  // 格式化价格显示
  it('formats prices correctly', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('¥5,999')).toBeInTheDocument();
    expect(screen.getByText('¥5,499')).toBeInTheDocument();
  });

  // 渲染规格信息
  it('renders spec values correctly', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('6GB')).toBeInTheDocument();
    expect(screen.getByText('8GB')).toBeInTheDocument();
    expect(screen.getByText('128GB')).toBeInTheDocument();
    expect(screen.getByText('256GB')).toBeInTheDocument();
    expect(screen.getByText('3349mAh')).toBeInTheDocument();
    expect(screen.getByText('4000mAh')).toBeInTheDocument();
  });

  // 屏幕信息格式
  it('renders screen info with size and refresh rate', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('6.1" 60Hz')).toBeInTheDocument();
    expect(screen.getByText('6.2" 120Hz')).toBeInTheDocument();
  });

  // 快充和主摄信息
  it('renders charging and camera info', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('20W')).toBeInTheDocument();
    expect(screen.getByText('25W')).toBeInTheDocument();
    expect(screen.getByText('48MP')).toBeInTheDocument();
    expect(screen.getByText('50MP')).toBeInTheDocument();
  });

  // 重量信息
  it('renders weight info', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    expect(screen.getByText('171g')).toBeInTheDocument();
    expect(screen.getByText('167g')).toBeInTheDocument();
  });

  // 差异高亮单元格样式
  it('applies highlight styling to different value cells', () => {
    render(<CompareTable phones={[phone1, phone2]} />);

    // 不同价格的单元格应该有 font-medium 样式
    const priceCell = screen.getByText('¥5,999');
    expect(priceCell).toHaveClass('font-medium');
  });

  // 相同值单元格不高亮
  it('does not apply highlight styling to same value cells', () => {
    const samePhone1 = createPhone({ id: 1, weight: 171 });
    const samePhone2 = createPhone({ id: 2, model: 'Other', weight: 171 });

    render(<CompareTable phones={[samePhone1, samePhone2]} />);

    // 重量相同 — 不应该有 font-medium
    const weightCells = screen.getAllByText('171g');
    weightCells.forEach((cell) => {
      expect(cell).not.toHaveClass('font-medium');
    });
  });

  // null 字段显示 '-' 而非 "nullGB" 等 (ISSUE-037)
  it('displays "-" for null fields instead of "nullGB"', () => {
    const nullPhone1 = createPhone({
      id: 1,
      ram: null as unknown as number,
      storage: null as unknown as number,
      battery: null as unknown as number,
      weight: null as unknown as number,
      charging: { wired: null as unknown as number, wireless: null as unknown as number },
      camera: { main: null as unknown as number, ultra: null as unknown as number, telephoto: null as unknown as number, front: null as unknown as number },
    });
    const nullPhone2 = createPhone({ id: 2, model: 'Other' });

    render(<CompareTable phones={[nullPhone1, nullPhone2]} />);

    // 不应出现 "nullGB" / "nullmAh" / "nullW" / "nullg"
    expect(screen.queryByText(/nullGB/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/nullmAh/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/nullW/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/nullg/i)).not.toBeInTheDocument();
    // 应有 '-' 占位
    expect(screen.getAllByText('-').length).toBeGreaterThan(0);
  });
});

// ISSUE-048：1TB 曾被截断为 1（GB 口径），数据修复为 1024 后对比表同样转 TB
describe('存储 TB 显示 (ISSUE-048)', () => {
  it('storage=1024 vs 256：TB 与 GB 混排，不出现 1024GB', () => {
    render(
      <CompareTable
        phones={[
          createPhone({ storage: 1024 }),
          createPhone({ id: 2, model: 'iPhone 16', storage: 256 }),
        ]}
      />
    );
    expect(screen.getByText('1TB')).toBeInTheDocument();
    expect(screen.getByText('256GB')).toBeInTheDocument();
    expect(screen.queryByText('1024GB')).not.toBeInTheDocument();
  });

  it('storage 缺失（undefined）双方显示 -', () => {
    render(
      <CompareTable
        phones={[createPhone({ storage: undefined }), createPhone({ id: 2, storage: undefined })]}
      />
    );
    expect(screen.getAllByText('-').length).toBeGreaterThan(0);
  });
});

// ISSUE-050：表头品牌去重（审查 F7：表头原为 {brand} {model} 直接拼接）
describe('表头品牌去重 (ISSUE-050)', () => {
  it('表头不出现品牌重复（真我Neo8 / 苹果iPhone 15）', () => {
    render(
      <CompareTable
        phones={[
          createPhone({ id: 1, brand: '真我', model: '真我Neo8' }),
          createPhone({ id: 2, brand: '苹果', model: '苹果iPhone 15' }),
        ]}
      />
    );
    // 表头与型号行都会出现该文本（行 cell 是 phone.model），用 getAllByText
    expect(screen.getAllByText('真我Neo8').length).toBeGreaterThan(0);
    expect(screen.getAllByText('苹果iPhone 15').length).toBeGreaterThan(0);
    expect(document.body.textContent).not.toContain('真我 真我');
    expect(document.body.textContent).not.toContain('苹果 苹果');
  });
});
