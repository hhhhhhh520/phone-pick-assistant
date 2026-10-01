/**
 * 存储格式化：数据库以 GB 为口径存整数。
 * 历史清洗曾把 "1TB" 截断为 1（ISSUE-048），数据侧已修复为 1024；
 * 展示层对 ≥1024 的整数倍转 TB 显示，其余保持 GB，空值显示 '-'。
 */
export const formatStorage = (value: number | null | undefined): string => {
  // 0/缺失均视为无数据，与旧版 falsy 判断及后端 `_format_storage` 语义对齐
  if (!value) return '-';
  if (value >= 1024 && value % 1024 === 0) return `${value / 1024}TB`;
  return `${value}GB`;
};
