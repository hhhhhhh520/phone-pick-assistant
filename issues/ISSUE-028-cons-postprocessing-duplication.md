# ISSUE-028 Cons 后处理逻辑重复

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）

## 问题描述

当 LLM 推荐输出缺少"缺点"/"不足"等关键词时，系统自动从数据库补充 cons 数据。这个逻辑在两处**完全重复**：

| 位置 | 行号 | 作用 |
|------|------|------|
| `backend/services/recommend.py` | 163-186 | 在 `recommend()` 方法内部，LLM 流式输出结束后 yield cons |
| `backend/api/routes/chat.py` | 169-184 | 在 `generate()` 异步生成器中，收集完 recommend chunks 后再次检查并追加 cons |

两处代码使用相同的关键词列表、相同的 JSON 解析逻辑、相同的格式化方式。

## 出现原因

1. `recommend.py` 中的 cons 后处理是 `8e77403 feat(recommend): 场景感知推荐逻辑优化` 添加的
2. `chat.py` 中的版本可能是更早的实现，或者是为了"双重保险"在路由层又加了一遍
3. 两处代码独立添加，没有意识到对方已经存在

## 当前执行流程分析

```
chat.py 调用 recommend_service.recommend()
  → recommend.py 内部：LLM 输出后检查 cons → 如果缺少则 yield cons_output
  → chat.py 收集所有 chunks 到 full_reply（此时 full_reply 已包含 recommend.py yield 的 cons）
  → chat.py 再次检查 full_reply 是否有 cons → 大多数情况下不会触发（因为已包含）
```

**结论**: `recommend.py` 的版本是源头，`chat.py` 的版本是冗余的保险机制。在正常流程中 `chat.py` 的检查几乎不会触发。

## 解决方案

**方案**: 从 `chat.py` 删除重复的 cons 后处理逻辑，保留 `recommend.py` 中的版本。

具体改动：
1. 删除 `chat.py:169-184` 的 cons 检查和追加代码
2. 保留 `recommend.py:163-186` 的版本（它是 cons 注入的源头）
3. 确认 `recommend.py` yield 的 cons chunk 能被 `chat.py` 正确收集到 `full_reply` 中（当前已满足）

**改动前** (`chat.py`):
```python
# 收集完整回复
full_reply = ""
async for chunk in recommend_service.recommend(sanitized_message, phones, history):
    full_reply += chunk
    yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

# 后处理：如果推荐内容缺少缺点披露，自动补充  ← 删除这整段
cons_keywords = ['不足', '缺点', '局限', '短板', '注意', '不过', '遗憾']
if not any(kw in full_reply for kw in cons_keywords):
    cons_lines = []
    for p in phones[:5]:
        ...
    if cons_lines:
        cons_output = "\n\n### 潜在不足\n" + "\n".join(cons_lines)
        full_reply += cons_output
        yield f"data: ..."
```

**改动后** (`chat.py`):
```python
# 收集完整回复（cons 后处理已在 recommend_service.recommend() 中完成）
full_reply = ""
async for chunk in recommend_service.recommend(sanitized_message, phones, history):
    full_reply += chunk
    yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
```

## 影响面

- 功能影响：无。删除的是冗余逻辑，`recommend.py` 已经处理了 cons 注入
- 测试影响：需要确认 `test_improvements.py` 中的 cons 相关测试仍然通过
- 风险等级：低。但需要验证 `recommend.py` 的 yield 确实被正确收集

## 验证方法

1. 运行现有测试：`pytest tests/test_improvements.py -v`
2. 手动测试：发送推荐请求，确认 LLM 输出缺少 cons 时，最终结果仍包含"潜在不足"段落
3. 检查 session 中存储的 `full_reply` 是否包含 cons 数据

## 相关文件

- `backend/services/recommend.py:163-186` — 保留（cons 注入源头）
- `backend/api/routes/chat.py:169-184` — 删除（冗余副本）

## 参考资料

- 相关提交: `8e77403 feat(recommend): 场景感知推荐逻辑优化`
- 相关测试: `tests/test_improvements.py`
