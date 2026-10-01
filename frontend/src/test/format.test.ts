import { describe, it, expect } from 'vitest';
import { formatStorage } from '../utils/format';

// ISSUE-048：历史清洗把 "1TB" 截断为 1（GB 口径），数据侧修复为 1024 后，
// 展示层需将 ≥1024 的整倍数转 TB 显示
describe('formatStorage (ISSUE-048)', () => {
  it('1024 → 1TB', () => {
    expect(formatStorage(1024)).toBe('1TB');
  });

  it('2048 → 2TB', () => {
    expect(formatStorage(2048)).toBe('2TB');
  });

  it('128 → 128GB', () => {
    expect(formatStorage(128)).toBe('128GB');
  });

  it('1536（非整TB倍数）→ 1536GB，不做小数 TB', () => {
    expect(formatStorage(1536)).toBe('1536GB');
  });

  it('null → -', () => {
    expect(formatStorage(null)).toBe('-');
  });

  it('undefined → -', () => {
    expect(formatStorage(undefined)).toBe('-');
  });

  it('0 → -（与旧版 falsy 行为及后端省略语义对齐）', () => {
    expect(formatStorage(0)).toBe('-');
  });
});
