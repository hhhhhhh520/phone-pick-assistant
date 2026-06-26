# ISSUE-033 死代码清理（6 处）

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）— 已删除全部 6 处死代码 + 23 个对应测试

## 问题描述

代码库中存在 6 处已定义但从未在生产代码中使用的代码：

| # | 代码 | 位置 | 状态 |
|---|------|------|------|
| 1 | `ChatErrorBoundary` 组件 | `frontend/src/components/ErrorBoundary.tsx:64-76` | 导出但从未导入 |
| 2 | `generate_multi_field_response` 方法 | `backend/services/question.py:254-294` | 从未调用，与 `generate_full_response` 逻辑重复 |
| 3 | `is_production` 属性 | `backend/config.py:36-38` | 定义但未使用，`main.py` 直接比较字符串 |
| 4 | `escape_for_prompt` 函数 | `backend/utils/security.py:126-142` | 仅在测试中引用，生产代码未使用 |
| 5 | `get_next_question_field` 方法 | `backend/services/need_analysis.py:206-238` | 仅在测试中引用，逻辑已在 `QuestionService._get_missing_field_names` 中实现 |
| 6 | `get_completion_percentage` 方法 | `backend/services/need_analysis.py:163-204` | 仅在测试中引用，可考虑暴露给前端做进度指示 |

## 出现原因

- 功能迭代过程中旧代码未清理（`generate_multi_field_response` 被 `generate_full_response` 替代）
- 开发时预留的接口后来没有使用（`ChatErrorBoundary`、`escape_for_prompt`）
- 重构后旧实现残留（`get_next_question_field`）

## 解决方案

**直接删除**（#1-#5）：
- 删除未使用的代码
- 删除仅引用这些代码的测试

**保留并评估**（#6）：
- `get_completion_percentage` 可能对前端进度指示有用
- 如果确认不需要，再删除

## 影响面

- 功能影响：无。删除的都是未使用的代码
- 测试影响：需要同步删除引用这些代码的测试用例
- 风险等级：零

## 验证方法

1. 删除后运行全量测试：`pytest tests/ -v && cd frontend && npm test`
2. 确认没有 import 错误
3. 确认前端构建正常：`cd frontend && npm run build`

## 相关文件

- `frontend/src/components/ErrorBoundary.tsx` — 删除 `ChatErrorBoundary`
- `backend/services/question.py` — 删除 `generate_multi_field_response`
- `backend/config.py` — 删除 `is_production`
- `backend/utils/security.py` — 删除 `escape_for_prompt`
- `backend/services/need_analysis.py` — 删除 `get_next_question_field`，评估 `get_completion_percentage`
