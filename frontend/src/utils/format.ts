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

/**
 * 展示名品牌去重 (ISSUE-050)：model 已含品牌前缀则原样使用（品牌出现一次），
 * 否则 brand + 空格 + model。与后端 domain.Phone.display_name 同语义。
 * 注意与 PhoneCard 的 displayModel（剥离品牌，因品牌行分行展示）用途不同。
 */
export const formatPhoneName = (
  brand: string | null | undefined,
  model: string | null | undefined
): string => {
  const b = brand ?? '';
  const m = model ?? '';
  if (!m) return b;
  if (b && m.startsWith(b)) return m;
  return `${b} ${m}`.trim();
};
