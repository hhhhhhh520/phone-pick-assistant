# ISSUE-011 搜索历史存储完整手机数据

> 创建时间: 2026-06-25
> 状态: ⏪ 已跳过（2026-06-25）

## 问题描述

`useSearchHistory.ts` 把完整手机对象（含价格、规格、图片 URL）存入 localStorage，数据量较大。

## 跳过原因

当前历史记录最多 10 条，数据量不大。改为按需获取会牺牲用户体验（点击历史需等待 API 请求）。不值得为此改动。

## 相关文件

- `frontend/src/hooks/useSearchHistory.ts`
