# ISSUE-034 测试覆盖缺口

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）— 后端 chat 路由 16 测试 + 前端 7 组件 84 测试
> 优先级: P2（不影响功能，但影响质量保障）

## 问题描述

代码审查发现多处测试覆盖不足，分为三类：前端组件无测试、后端核心路由无专用测试、测试质量问题。

### 一、前端组件无测试（6 个）

| 组件 | 行数 | 缺失内容 |
|------|------|----------|
| `CompareTable.tsx` | 164 | 对比表格渲染、差异高亮、边界情况 |
| `PhoneCard.tsx` | ~100 | 手机卡片渲染、图片 fallback、评分显示、标签展示 |
| `InputBar.tsx` | ~50 | 表单提交、空输入防护、取消按钮、Enter 键提交 |
| `MessageList.tsx` | ~80 | 空状态渲染、消息排序、自动滚动 |
| `SearchHistory.tsx` | ~80 | 历史记录渲染、时间格式化、清除功能 |
| `hooks/useSearchHistory.ts` | ~30 | localStorage 持久化 |
| `hooks/useSession.ts` | ~20 | session ID 持久化 |

### 二、后端核心路由无专用测试

`backend/api/routes/chat.py`（229 行）只有 `test_chat_flow.py` 测试多轮对话流程，缺少：

- `compare` 意图分支：检索手机、对比输出
- `filter` 意图分支：预算筛选
- cons 后处理逻辑：LLM 输出缺少缺点时自动补充
- `ModelParserService` 过滤逻辑：只发送被推荐的手机
- 速率限制：`@limiter.limit("20/minute")` 行为

### 三、测试质量问题

| 问题 | 位置 | 描述 |
|------|------|------|
| 弱断言 | `test_llm_context.py:37` | `assert estimate_tokens("a") >= 0` 永远为真 |
| 硬编码计数 | `test_data_completeness.py:169` | 硬编码 353 条记录，数据变化即崩溃 |
| 无效 E2E 测试 | `e2e_test_multi_turn.py` | 不是 pytest 文件，硬编码端口 8003 |
| Mock 不完整 | `test_intent_service_enhanced.py:206` | 跳过 SSE 流式解析测试 |

## 出现原因

MVP 阶段优先实现功能，测试延后。前端组件和 chat 路由是核心功能，但没有对应的测试文件。

## 解决方案

### 高优先级（先做）

1. **补充 `chat.py` 路由测试** — 创建 `tests/test_chat_route.py`，覆盖 recommend/compare/filter 三个分支
2. **修复弱断言** — `test_llm_context.py:37` 改为 `assert estimate_tokens("a") >= 1`
3. **修复硬编码计数** — `test_data_completeness.py:169` 改为动态获取或移除精确计数断言

### 中优先级

4. **补充前端组件测试** — 按组件逐个补充，优先 `CompareTable` 和 `PhoneCard`
5. **重写 E2E 测试** — 改为 pytest-asyncio 格式，使用 httpx.TestClient

### 低优先级

6. **补充 hooks 测试** — 使用 `renderHook` 测试自定义 hooks

## 影响面

- 功能影响：无。这是测试补充，不改生产代码
- 风险等级：零

## 相关文件

- `tests/test_chat_route.py` — 新建
- `tests/test_llm_context.py:37` — 修复断言
- `tests/test_data_completeness.py:169` — 修复硬编码
- `tests/e2e_test_multi_turn.py` — 重写
- `frontend/src/test/CompareTable.test.tsx` — 新建
- `frontend/src/test/PhoneCard.test.tsx` — 新建
- `frontend/src/test/InputBar.test.tsx` — 新建
- `frontend/src/test/MessageList.test.tsx` — 新建
- `frontend/src/test/SearchHistory.test.tsx` — 新建
