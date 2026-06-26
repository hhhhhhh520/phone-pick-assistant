# ISSUE-035 CORS 配置硬编码 12 个 localhost 变体

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）

## 问题描述

`backend/config.py:29` 的默认 `cors_origins` 值包含 12 个 localhost 端口变体：

```python
cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:5177,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:5176,http://127.0.0.1:5177,http://127.0.0.1:3000"
```

## 出现原因

开发过程中前端端口变化（Vite 默认 5173，有时用 5174-5177，React 默认 3000），每次都往列表里加一个新条目。

## 解决方案

简化为实际需要的端口，或使用环境变量覆盖：

```python
# 默认只保留开发环境常用的两个端口
cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

# 生产环境通过 .env 文件覆盖
# CORS_ORIGINS=https://your-domain.com
```

## 影响面

- 功能影响：无。开发环境只需要一个前端端口
- 风险等级：零

## 相关文件

- `backend/config.py:29` — 简化默认值
