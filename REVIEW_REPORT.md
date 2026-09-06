# Phone-Pick-Assistant 多维度审查报告

> **时点备注（2026-09-06 补充）**: 本文为 2026-06-28 的审查快照。其中 C1/C2/C3/C5/C6 已于 2026-06-28 修复，C7/H2 经核实已在 2026-06-27 修复（见 PROGRESS.md「2026-06-28 多维度审查 + 数据修复」的修复与假阳性记录）；C4 经讨论确认不修复，C8 仍在待办中，其余各项以 PROGRESS.md 后续记录为准。阅读时请注意时点。

> 审查日期: 2026-06-28 | 审查角度: 代码质量、安全、数据质量、前端契约、测试覆盖

---

## 审查总览

| 维度 | CRITICAL | HIGH | MEDIUM | LOW | 总计 |
|------|----------|------|--------|-----|------|
| 安全审查 | 1 | 3 | 3 | 2 | 9 |
| 数据质量与业务逻辑 | 5 | 5 | 7 | 3 | 20 |
| 前端与 API 契约 | 2 | 0 | 6 | 5 | 13 |
| **合计** | **8** | **8** | **16** | **10** | **42** |

**整体健康度评分: 5.5/10** — 功能基本可用，但数据质量问题严重影响核心推荐准确性。

---

## 一、CRITICAL 问题（必须修复）

### C1. RAM 字段含爬虫残留文本 — 47.9% 手机内存数据失效
- **来源**: 数据质量审查
- **位置**: `phones.db` + `backend/services/retrieval.py`
- **问题**: 169 款手机的 RAM 字段为 NULL，另有数据包含 `'12GB游戏运行良好大于78.29%手机内存行业最高：24G＞'` 等垃圾文本
- **影响**: SQLAlchemy Integer 列无法转换文本值，返回 None → `_safe_ram_value()` 返回 0 → 游戏/性能排序失效
- **修复**: 数据清洗脚本提取数值，添加入库验证

### C2. 电池字段含多余文本 — 续航排序和过滤失效
- **来源**: 数据质量审查
- **位置**: `phones.db` + `backend/services/retrieval.py:352`
- **问题**: 电池字段包含 `'5000mAh电池类型：不可拆卸式电池'`、`'7000mAhmAh'` 等
- **影响**: SQLite 中 TEXT >= INTEGER 永远为 TRUE，`battery >= 5000` 过滤器对文本值失效
- **修复**: 数据清洗 + `_safe_battery_value()` 应用于所有查询

### C3. 影像评分字段 100% 为空 — 拍照评分系统完全失效
- **来源**: 数据质量审查
- **位置**: `backend/services/camera_score.py` + `phones.db`
- **问题**: `telephoto_type`、`image_brand`、`has_ois` 全部 NULL（353/353），`sensor_main` 91.8% 为 NULL
- **影响**: 硬件维度 35 分全部丢失，评分只剩芯片分 + 品牌默认算法分
- **修复**: 补全 `seed.py` 中的 `IMAGE_CONFIG` 数据，或从外部数据源爬取

### C4. 品牌映射不一致 — "小米"搜索丢失 20 款红米手机
- **来源**: 数据质量审查
- **位置**: `backend/services/intent.py:217` + `backend/services/retrieval.py`
- **问题**: `intent.py` 将 "小米" 和 "红米" 都映射为 `["小米"]`，但数据库中是两个独立品牌
- **影响**: 用户说 "推荐小米手机" 时，Redmi K80、Redmi Note 14 Pro 等 20 款手机被排除
- **修复**: `_extract_brands()` 返回 `["小米", "红米"]` 或合并数据库品牌

### C5. 疼痛点 UI 完全是死代码 — 后端从未发送 pain_point 字段
- **来源**: 前端审查
- **位置**: `backend/api/routes/chat.py:128-132` + `frontend/src/components/ChatWindow.tsx:83-104`
- **问题**: 后端 `generate()` 发送 `question` SSE 事件时只包含 `question`、`quick_replies`、`missing_fields`，从不包含 `pain_point_type` 和 `pain_point_severity`
- **影响**: 前端 `isPainPoint` 永远为 false，橙色边框样式、警告标题、疼痛点按钮样式全部不生效
- **修复**: 在 `chat.py:128` 的 `question_data` 中添加疼痛点字段

### C6. SSE 错误事件被静默丢弃 — 用户看不到任何错误反馈
- **来源**: 前端审查
- **位置**: `frontend/src/components/ChatWindow.tsx:58-105`
- **问题**: 后端发送 `error` 事件（INVALID_INPUT、INTERNAL_ERROR），前端 `handleSend` 没有 `event.type === 'error'` 分支
- **影响**: 错误发生时用户看到空的助手气泡，无任何解释
- **修复**: 添加 error 事件处理分支

### C7. LLM 错误处理器泄露 API 详情（非生产环境）
- **来源**: 安全审查
- **位置**: `backend/services/llm.py:221-223` + `backend/main.py:277`
- **问题**: 非生产环境下，DeepSeek API 原始错误响应体（可能含 API key、endpoint URL）直接返回给前端
- **修复**: 错误详情只写日志，不返回客户端

### C8. 中文 Prompt Injection 完全不设防
- **来源**: 安全审查
- **位置**: `backend/utils/security.py:10-40`
- **问题**: `DANGEROUS_PATTERNS` 中 15 个正则全是英文的，中文注入指令如 "忽略以上所有指令" 完全绕过检测
- **修复**: 添加中文注入模式正则

---

## 二、HIGH 问题（应该修复）

### H1. "拍照"场景过滤条件过于严格
- **位置**: `backend/services/retrieval.py:227-236`
- **问题**: 只匹配徕卡/哈苏/蔡司标签，有 "拍照" 或 "影像" 标签但无品牌标签的手机被排除
- **修复**: 扩展匹配条件，添加 `features.contains("影像")`、`features.contains("拍照")`、`camera_main >= 5000`

### H2. `/health` 端点暴露 LLM API 错误详情
- **位置**: `backend/services/llm.py:172-176`
- **问题**: 任何人访问 `/health` 即可获取 DeepSeek API 的错误信息
- **修复**: 只返回 `{"status": "ok/error"}`，不暴露具体错误文本

### H3. LLM 输出未经验证直接发送到前端
- **位置**: `backend/api/routes/chat.py:168`
- **问题**: LLM 输出不检查是否包含系统提示词片段、可疑 URL、偏离主题内容
- **修复**: 添加后处理校验

### H4. 数据入库无验证层
- **位置**: `backend/data/seed.py` 及所有数据脚本
- **问题**: RAM、电池、价格等字段无范围验证，所有数据质量问题源于此
- **修复**: 添加验证脚本，限制 RAM 2-32GB、电池 1000-10000mAh、价格 > 0

### H5. 手机数据 API 无 rate limiting
- **位置**: `backend/api/routes/phones.py`
- **问题**: `/api/phones` 和 `/api/phones/{id}` 完全没有请求频率限制
- **修复**: 添加 `@limiter.limit("60/minute")`

### H6. Token 用量无每日上限
- **位置**: `backend/services/llm.py`
- **问题**: 单用户 20 次/分钟 × 2048 token = 每小时约 2.4M token，API 费用不受控
- **修复**: 添加每日 token 消耗计数器

### H7. 非生产环境通用异常泄露异常类型
- **位置**: `backend/main.py:296-302`
- **问题**: 异常类名和消息直接返回，可能含文件路径等敏感信息
- **修复**: 非生产环境也只返回 error code

### H8. 注入检测暴露匹配模式
- **位置**: `backend/utils/security.py:94`
- **问题**: `match.group()` 返回具体匹配到的正则模式，攻击者可推断所有规则
- **修复**: 返回模糊的 "输入包含不允许的内容"

---

## 三、MEDIUM 问题（建议修复）

| # | 维度 | 位置 | 问题 |
|---|------|------|------|
| M1 | 数据 | phones.db | 3 个重复型号（Redmi K80 Pro、Note 13 Pro、Note 15 Pro） |
| M2 | 前端 | api.ts:76-90 | `getPhones` 返回类型与后端不匹配（Phone vs PhoneBrief） |
| M3 | 前端 | api.ts:76-95 | `getPhones`/`getPhone` 从未被调用（死代码） |
| M4 | 前端 | ChatWindow.tsx | AbortController 未在组件卸载时清理（资源泄漏） |
| M5 | 前端 | PhoneCard.tsx:6 | onClick 定义但从未传递，光标样式误导 |
| M6 | 前端 | api.ts:88-95 | 缺少 `response.ok` 检查 |
| M7 | 前端 | ChatWindow.tsx, api.ts | 生产代码中的 `console.log` |
| M8 | 业务 | retrieval.py:249-251 | "性能"场景无数据库过滤，所有手机都是候选 |
| M9 | 业务 | intent.py `_extract_budget()` | 中文数字解析缺口：一万五、两万、五六千、3k、1.5万 |
| M10 | 业务 | recommend.py:86-93 | 空字段在 LLM prompt 中被省略，LLM 无法感知数据缺失 |
| M11 | 业务 | intent.py:452 | 疼痛点检测从未传入手机数据，使用硬编码价格参考 |
| M12 | 业务 | camera_score_config.py:9 | 文档说硬件权重 40%，实际满分 35/95 |
| M13 | 安全 | main.py:296 | 非生产环境异常类型泄露 |
| M14 | 业务 | retrieval.py | "拍照"过滤器过于严格（见 H1） |
| M15 | 安全 | llm.py | Token 无每日上限（见 H6） |
| M16 | 安全 | phones.py | API 无 rate limit（见 H5） |

---

## 四、LOW 问题（可选修复）

| # | 维度 | 位置 | 问题 |
|---|------|------|------|
| L1 | 数据 | phones.db | Sony Xperia Pro-i 价格=0 |
| L2 | 前端 | useSearchHistory.ts:23 | localStorage 存储完整 Phone 对象，可能超限 |
| L3 | 前端 | CompareTable.tsx:12 | 超过 2 款手机时静默忽略 |
| L4 | 前端 | MessageList.tsx:26-31 | 每个 chunk 都触发 scrollIntoView |
| L5 | 前端 | api.ts:63-68 | JSON 解析错误被静默吞没 |
| L6 | 前端 | types/index.ts:26 | camera 类型缺少后端返回的 5 个字段 |
| L7 | 业务 | session.py | 多轮对话偏好冲突时静默覆盖 |
| L8 | 业务 | chat.py + errors.py | SSE 与 HTTP 错误格式不一致 |
| L9 | 业务 | chat.py | Rate limit 配置与文档不一致 |
| L10 | 安全 | app.log | httpx INFO 日志泄露完整 API URL |

---

## 五、正面发现

| 维度 | 评估 | 说明 |
|------|------|------|
| SQL 注入 | ✅ 安全 | 全部使用 SQLAlchemy ORM 参数化查询 |
| XSS | ✅ 安全 | React JSX 自动转义，无 dangerouslySetInnerHTML |
| CORS | ✅ 安全 | 白名单模式，默认只允许 localhost |
| API Key | ✅ 安全 | .env 已被 .gitignore 排除 |
| 生产错误处理 | ✅ 安全 | production 环境所有异常详情返回 None |
| Rate Limiting | ⚠️ 部分 | /api/chat 有 20/分钟限制 |
| 输入验证 | ⚠️ 部分 | 有长度限制、控制字符过滤、注入模式检测 |
| 测试覆盖 | ⚠️ 部分 | 后端 33 个测试文件，前端无测试 |

---

## 六、修复优先级

### P0 — 立即修复（影响核心功能）
1. **C1+C2**: RAM/电池数据清洗（一个迁移脚本）
2. **C4**: 品牌映射修复（`intent.py` 一行改动）
3. **C5**: 疼痛点字段发送（`chat.py` 几行改动）
4. **C6**: SSE 错误处理（前端几行改动）
5. **C8**: 中文 Prompt Injection 防御

### P1 — 尽快修复（影响数据质量和安全）
6. **C3**: 影像评分字段补全
7. **H1**: 拍照过滤器扩展
8. **H4**: 数据入库验证
9. **C7+H2**: 错误信息泄露修复

### P2 — 计划修复
10. **M8-M9**: 性能过滤 + 中文数字解析
11. **M3**: 死代码清理
12. **H5-H6**: Rate limit + Token 上限

### P3 — 低优先级
13. 前端 UX 优化（L2-L6）
14. 文档同步（M12）
15. 日志清理（M7, L10）

---

## 七、测试覆盖评估

- **后端**: 33 个测试文件，覆盖意图识别、检索、安全、会话等核心模块
- **前端**: 无测试文件
- **缺口**:
  - 无数据质量回归测试
  - 无 E2E 测试覆盖完整对话流程
  - 无前端组件测试
  - 无 API 契约测试
