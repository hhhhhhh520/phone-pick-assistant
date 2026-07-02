# 对比表格数据质量硬伤：null拼接 + 单位解析错误
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

对比模式 "小米14 Ultra vs 华为Mate 70 Pro" 生成的参数表格暴露大量脏数据：

| 字段 | 实际显示 | 正确值/问题 |
|------|----------|------------|
| 存储 | "1GB" / "nullGB" | 1TB 被解析成 1GB；None 直接拼成 "nullGB" |
| 屏幕刷新率 | "nullHz" | None 字符串拼接 |
| 快充 | "nullW" | 两款旗舰都缺数据 |
| 重量 | "4g" / "nullg" | 小米14 Ultra 4g（明显错误，疑为清洗把"200+"弄成"4"）；None 拼成 "nullg" |
| 屏幕 | "6.9英寸纠错\"" | 数据清洗残留"纠错"字样未去净 |

## 出现原因

1. **None 拼接**：`Phone.to_dict()` 对空值字段直接做 `f"{value}{unit}"` 字符串拼接，None 被转成字符串 "null"，产生 "nullGB""nullHz""nullW""nullg"。
2. **单位换算 bug**：1TB 存储被解析成 1GB，存储单位判断逻辑（GB/TB）有错。
3. **数据清洗残留**：屏幕字段"6.9英寸纠错"——爬取/清洗时未去掉源页面的"纠错"按钮文本。
4. **重量数据错误**：小米14 Ultra 重量 4g，疑似数据清洗脚本误处理（TEST_CHECKLIST D4 记录的努比亚小牛"5g"同类问题）。

## 解决方案

1. `to_dict()` 对 None 值返回空字符串或"-"，禁止 `f"{value}{unit}"` 裸拼接
2. 存储单位解析修复（TB/GB 区分）
3. 屏幕字段清洗去掉"纠错"等残留词
4. 重量字段回查数据源修正

## 相关文件

- `backend/models/domain.py`（`Phone.to_dict` 单位拼接逻辑）
- `backend/data/`（清洗脚本）

## 参考资料

- TEST_CHECKLIST.md D3/D4 已记录类似数据错误
- PROGRESS.md P6：processor 286 条缺失、camera_main 324 条缺失
- 实测：2026-07-02 无头浏览器测试发现
