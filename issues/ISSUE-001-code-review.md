# 代码审查问题清单

> 创建时间: 2026-04-29
> 状态: 🟢 大部分已解决（20 项中 17 项已修复，剩余 3 项为非阻塞优化建议）

## 问题描述

项目代码审查发现 5 个 Blocker、8 个 Suggestion、5 个 Nit 级别的问题，详见下方分类。

---

## 🔴 Blockers（必须修复）

### ISSUE-001: 会话服务并发安全问题

**位置**: `backend/services/session.py:9`

**问题描述**: 使用模块级全局字典存储会话，多线程/多进程环境下存在竞态条件。FastAPI 默认多线程处理请求，复合操作如 `sessions[session_id].append()` 不是原子操作。如果部署使用多 worker，每个进程有独立内存空间，会话数据无法共享。

**出现原因**: 设计时未考虑并发场景，使用了简单的内存字典存储。

**解决方案**:
1. 使用 `threading.Lock` 保护读写操作
2. 或改用 Redis 存储，支持分布式部署

**相关文件**:
- `backend/services/session.py`

---

### ISSUE-002: 会话存储内存泄漏

**位置**: `backend/services/session.py:19-23`

**问题描述**: 会话创建后永不清理，长期运行内存持续增长。每个新用户访问都会创建新会话，没有过期时间、没有清理机制。

**出现原因**: 缺少会话生命周期管理机制。

**解决方案**:
1. 添加会话过期时间（如30分钟不活跃自动删除）
2. 实现定期清理过期会话的后台任务

**相关文件**:
- `backend/services/session.py`

---

### ISSUE-003: LLM服务缺少HTTP错误处理

**位置**: `backend/services/llm.py:22-43`

**问题描述**: `chat_stream` 方法未检查 `response.status_code`，DeepSeek API 返回 4xx/5xx 错误时无法正确处理。API 密钥过期、配额用尽、服务不可用等情况不会得到正确处理，上层调用者无法区分"LLM返回空内容"和"请求失败"。

**出现原因**: 只考虑了正常流程，未处理网络请求失败场景。

**解决方案**:
```python
async with client.stream(...) as response:
    if response.status_code != 200:
        error_body = await response.aread()
        raise LLMError(f"API error: {response.status_code}, {error_body}")
    # 继续处理...
```

**相关文件**:
- `backend/services/llm.py`

---

### ISSUE-004: 意图识别降级处理不当

**位置**: `backend/services/intent.py:42-53`

**问题描述**: JSON 解析失败时返回默认 IntentResult，丢失用户输入的预算、品牌等关键信息。用户说"3000元以下推荐华为"如果 LLM 返回格式错误，系统会返回所有手机而非按条件筛选，用户期望被完全忽略。

**出现原因**: 异常处理过于简单，只返回默认值而未保留任何上下文。

**解决方案**:
1. 记录原始 LLM 响应用于调试
2. 考虑使用重试机制
3. 或降级到基于规则的意图识别

**相关文件**:
- `backend/services/intent.py`

---

### ISSUE-005: phones.py 统计逻辑问题

**位置**: `backend/api/routes/phones.py:28-29`

**问题描述**: `total` 计算逻辑混淆，且缺少输入参数验证（负数 limit、不存在的 brand）。

**出现原因**: 代码逻辑不清晰，缺少输入校验。

**解决方案**:
1. 添加参数验证（limit > 0, brand 存在性检查）
2. 明确 total 计算逻辑

**相关文件**:
- `backend/api/routes/phones.py`

---

## 🟡 Suggestions（应该修复）

### ISSUE-006: 服务实例化不一致

**位置**: `backend/api/routes/chat.py:14-25`

**问题描述**: `session_service` 是模块级实例，但 `intent_service`、`retrieval_service`、`recommend_service` 每次请求创建新实例。实例化策略不一致，难以理解设计意图。

**解决方案**: 统一服务生命周期管理，使用依赖注入。

**相关文件**:
- `backend/api/routes/chat.py`

---

### ISSUE-007: 模块级 settings 实例导致测试困难

**位置**: `backend/services/llm.py:6`

**问题描述**: 模块导入时配置被固定，无法在测试中替换，无法动态修改配置。

**解决方案**: 在 `__init__` 中获取 settings，或通过构造函数传入。

**相关文件**:
- `backend/services/llm.py`

---

### ISSUE-008: domain.py 职责混合

**位置**: `backend/models/domain.py:69-84`

**问题描述**: 数据模型和数据库初始化逻辑耦合在同一文件，违反单一职责原则，导入 Phone 模型时就会创建数据库连接，测试时难以替换数据库。

**解决方案**: 将数据库初始化移到单独的 `database.py` 模块。

**相关文件**:
- `backend/models/domain.py`

---

### ISSUE-009: 前端 API 地址硬编码

**位置**: `frontend/src/services/api.ts:3`

**问题描述**: `const API_BASE = 'http://localhost:8000';` 无法根据环境切换，部署时需要修改代码。

**解决方案**: 使用环境变量 `import.meta.env.VITE_API_BASE`。

**相关文件**:
- `frontend/src/services/api.ts`

---

### ISSUE-010: 缺少请求取消机制

**位置**: `frontend/src/components/ChatWindow.tsx`

**问题描述**: 流式请求没有取消机制，用户离开页面请求不中断。

**解决方案**: 使用 AbortController 管理请求。

**相关文件**:
- `frontend/src/components/ChatWindow.tsx`

---

### ISSUE-011: 搜索历史信息泄露风险

**位置**: `frontend/src/hooks/useSearchHistory.ts`

**问题描述**: 完整手机数据存入 localStorage，可能被 XSS 窃取。

**解决方案**: 只存储摘要信息，使用 sessionStorage。

**相关文件**:
- `frontend/src/hooks/useSearchHistory.ts`

---

### ISSUE-012: CORS 配置过于宽松

**位置**: `backend/main.py:21-28`

**问题描述**: 硬编码大量 localhost 端口，生产环境不适用。

**解决方案**: 从配置文件读取允许的 origins。

**相关文件**:
- `backend/main.py`

---

### ISSUE-013: Prompt 注入风险

**位置**: `backend/services/intent.py:39`

**问题描述**: 用户输入直接插入 prompt 模板，可能格式化错误或注入。

**解决方案**: 对用户输入进行转义或验证。

**相关文件**:
- `backend/services/intent.py`

---

## 🔵 Nits（建议改进）

| # | 问题 | 位置 |
|---|------|------|
| 14 | ChatRequest 缺少输入长度验证 | `backend/models/schemas.py` |
| 15 | 错误消息直接暴露给用户 | `frontend/src/components/ChatWindow.tsx:75` |
| 16 | 缺少日志记录 | 整个后端 |
| 17 | 推荐服务 history 可能导致上下文膨胀 | `backend/services/recommend.py:68-70` |
| 18 | 缺少统一错误处理机制 | 后端全局 |
| 19 | `/health` 端点不检查依赖项 | `backend/main.py` |
| 20 | 前端缺少 Error Boundary | `frontend/src/App.tsx` |

---

## 修复优先级

1. **会话并发安全 + 内存泄漏**（ISSUE-001, ISSUE-002）→ 最紧急
2. **LLM 错误处理**（ISSUE-003）
3. **意图识别降级**（ISSUE-004）
4. **服务实例化重构**（ISSUE-006, ISSUE-007, ISSUE-008）

---

## 参考资料

- 代码审查使用 Code Reviewer Agent 完成
- 审查范围：后端核心文件 + 前端核心组件
