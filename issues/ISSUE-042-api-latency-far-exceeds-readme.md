# API响应时间远超README宣称，/health单次2.9秒
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

README 宣称"平均响应时间 ~200ms"，实测：

| 端点 | 单请求延迟 | 50并发 |
|------|-----------|--------|
| `GET /api/phones?limit=5` | **2035ms** | 平均2076ms，全部200 |
| `GET /health` | **2927ms** | — |

单请求就要 2 秒，与"200ms"差 10 倍。

## 出现原因（待确认，仅记录不深挖）

1. **`/health` 慢**：虽然有 60s LLM 缓存（PROGRESS 06-27 修复），但缓存未命中时同步调用 DeepSeek API 做健康检查，单次近 3 秒。健康检查本应是轻量操作。
2. **`/api/phones` 慢**：SQLite 本地查询不该 2 秒。可能原因：
   - 每次请求新建 DB session / 连接开销
   - `to_dict()` 或其他序列化逻辑有隐藏耗时
   - 中间件（CORS、rate limiter、日志）开销
   - 需进一步 profile 确认根因

## 解决结果（2026-07-02）

经 profile 定位：
- **`/api/phones` 的 2s 是冷启动首请求误判**：import app 阶段耗时 1139ms（加载 antutu JSON/pydantic/SQLAlchemy），稳态请求 ~205ms，与 README 200ms 标称基本一致。无需修复。
- **`/health` 的 1.66s 是真问题**：缓存未命中时同步调 LLM 阻塞。已改为后台异步刷新（`refresh_llm_health_periodically`），请求永远读 `_llm_health` 缓存，首次请求降至 0.21s，HTTP 永远 200（不触发容器重启）。LLM 监控信号保留。

## 影响

- 用户体验差，列表页加载需 2 秒+
- README 性能指标失真，误导评估

## 解决方案

需先 profile 定位根因（不要瞎改）：
1. 对 `/api/phones` 加耗时日志，拆分 DB 查询 / 序列化 / 中间件各占多少
2. `/health` 的 LLM 检查改为异步或降频，健康检查不应阻塞 3 秒
3. 确认 SQLAlchemy session 是否复用连接池

## 相关文件

- `backend/main.py`（`/health` 端点、中间件）
- `backend/api/routes/phones.py`（列表查询）
- `backend/api/dependencies.py`（DB session）

## 参考资料

- README 称"平均响应时间 ~200ms"、"50并发100%成功率"
- 实测：2026-07-02，50并发成功率确实100%，但延迟2秒+
