# ISSUE-027 生产代码中残留 print("[DEBUG]") 调试语句

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）

## 问题描述

`backend/services/recommend.py` 中有 3 处 `print(f"[DEBUG]...")` 语句，会将调试信息输出到生产环境 stdout，暴露内部状态（content_len、has_cons、phones 数量）。

**位置**:
- `backend/services/recommend.py:166` — `print(f"[DEBUG] Post-process: content_len={len(full_content)}, has_cons={has_cons}")`
- `backend/services/recommend.py:181` — `print(f"[DEBUG] Post-process: adding cons for {len(cons_lines)} phones")`
- `backend/services/recommend.py:185` — `print("[DEBUG] Post-process: no cons data available")`

同位置已有 `logger.info()` 记录相同信息，`print` 完全冗余。

## 出现原因

开发调试 cons 后处理逻辑时添加了 print 语句用于快速验证，提交时忘记删除。该逻辑在 `8e77403 feat(recommend): 场景感知推荐逻辑优化` 提交中加入。

## 解决方案

直接删除 3 行 `print` 语句，保留同位置的 `logger.info()` 调用。

```python
# 删除这 3 行：
print(f"[DEBUG] Post-process: content_len={len(full_content)}, has_cons={has_cons}", flush=True)
print(f"[DEBUG] Post-process: adding cons for {len(cons_lines)} phones", flush=True)
print("[DEBUG] Post-process: no cons data available", flush=True)
```

## 影响面

- 功能影响：无。print 只输出到 stdout，不影响任何逻辑
- 测试影响：无。没有任何测试依赖 print 输出
- 风险等级：零

## 相关文件

- `backend/services/recommend.py` — 删除 3 行 print

## 参考资料

- 相关提交: `8e77403 feat(recommend): 场景感知推荐逻辑优化`
