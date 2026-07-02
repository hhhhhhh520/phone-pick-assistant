# 手机选购助手 - 项目进度

> 创建时间: 2026-04-28 | 最后更新: 2026-07-02（无头浏览器实测 + 10项修复）

## 项目概述

**项目地址**: D:\my project\phone-pick-assistant
**技术栈**: FastAPI + React 19 + DeepSeek API + SQLite
**当前状态**: 功能完成，代码质量优化中

---

## 当前待办

| 优先级 | 任务 | 说明 | 相关 Issue |
|--------|------|------|-----------|
| P2 | chat.py 架构重构 | 120 行业务逻辑拆分为 ChatOrchestrator | ISSUE-032 |
| P2 | 中文 Prompt Injection 防御 | 当前仅英文正则，中文注入绕过 | REVIEW_REPORT C8 |
| P2 | 补充 sensor_main/telephoto_type 数据 | 仅 26 款旗舰有精确数据，327 款缺 | — |
| P3 | 前端无测试 | 缺少组件测试和 E2E 测试 | — |
| P6 | 补充 processor 数据 | 286 条缺失，需外部数据源 | — |
| P6 | 补充 camera_main 数据 | 324 条缺失，需外部数据源 | — |

---

## 2026-07-02 无头浏览器实测 + 10 项修复（ISSUE-036~045）

用 Playwright MCP 对 36 个场景做端到端实测，发现 10 个问题，安全审查方案后全部修复。后端 775 tests + 前端 125 tests 全过。

### 修复清单

| ISSUE | 修复内容 | 改动文件 |
|-------|----------|----------|
| 036 | 拍照推荐回退失效：新增 `search_with_fallback` 分级回退（保留预算+场景排序），拍照关键词扩展"影像/潜望长焦/大底"，新增 notice SSE 事件 | retrieval.py, chat.py, types/index.ts, ChatWindow.tsx, MessageItem.tsx |
| 037 | 对比表 null 拼接：CompareTable 加 `formatUnit` 格式化函数，null 显示"-" | CompareTable.tsx |
| 038 | 品牌名重复：PhoneCard 加 `displayModel` 去重 + null guard | PhoneCard.tsx |
| 039 | 对比虚构型号静默回退：型号找不到时不调 `compare([])`，发 notice 提示"未找到机型" | chat.py |
| 040 | 本地图片+号404：`getFullImageUrl` 加 `encodeURI().replace(/\+/g,'%2B')`，防双重编码 | PhoneCard.tsx |
| 041 | 列表/详情字段契约不一致：PhoneBrief 加 imageUrl 字段 | schemas.py, phones.py |
| 042 | /health 阻塞 1.66s：改后台异步刷新 LLM（`refresh_llm_health_periodically`），请求读缓存，HTTP 永远 200 | main.py |
| 043 | 排序参数未实现：list_phones 加 `sort` Query（pattern 校验），order_by 升/降序 | phones.py |
| 044 | PhoneCard onClick 未接线：去除 role=button/tabIndex/onKeyDown/onClick 交互伪装 | PhoneCard.tsx, MessageItem.tsx |
| 045 | 末尾空气泡：bottomRef 锚点加 `aria-hidden` + `height:0` | MessageList.tsx |

### 安全审查纠正的关键错误

- 方案2 保留 camelCase（不改 image_url），避免 213 款图片全失效
- 方案2 保留 to_dict 嵌套结构，避免 CompareTable 崩溃
- 方案1 compare 空列表走独立路径，避免 LLM 幻觉
- 方案5 /health 保持 HTTP 200，避免触发容器重启循环

---

## 2026-06-25 全面代码审查

使用 5 个并行专项审查 Agent（Critical Pass、Security、Performance、Testing、Maintainability）对全量代码库进行多角度审查。

**审查结果**: 原始发现 41 个 → 验证后真实问题 17 个（排除 5 个假阳性）

### 已修复（9 项，759 tests passed）

| ISSUE | 修复内容 | 改动 |
|-------|----------|------|
| 027 | 删除 `recommend.py` 中 3 处 `print("[DEBUG]")` | 删除 3 行 |
| 028 | 删除 `chat.py` 中重复的 cons 后处理逻辑 | 删除 16 行 |
| 029 | 抽取 `_find_matching_key` 公共方法消除 antutu 函数重复 | 重构 ~120 行 |
| 030 | 抽取 `_parse_json_field` 静态方法消除 to_dict 重复 | 重构 ~40 行 |
| 031 | 4 处 `import re/random` 从函数内移到模块级 | 4 个文件 |
| 033 | 删除 `ChatErrorBoundary` + `is_production` 死代码 | 2 个文件 |
| 035 | CORS 从 12 个 localhost 简化为 2 个 | config.py |
| — | `_extract_budget` 正则 bug（"X万以下" 匹配失败） | intent.py 2 行 + 12 测试 |
| — | `test_logging.py` 方法名过时（`_call_api` → `chat`） | test_logging.py 1 行 |

### 假阳性（不是问题）

| 原始发现 | 原因 |
|----------|------|
| `question.py:189` IndexError | 受调用方 `question.py:271` 的守卫保护 |
| `llm.py` tiktoken 每次探测 | Python import 缓存，非热路径 |
| `llm.py` httpx 每次新建客户端 | `async with` 是 httpx 正确用法 |
| `dependencies.py` 单例竞态 | FastAPI 单线程事件循环 |
| `session.py` 模块级全局状态 | FastAPI 单例服务标准做法 |

---

## 2026-06-28 多维度审查 + 数据修复

5 个并行 Agent（代码质量、安全、数据质量、前端契约、测试覆盖）从不同角度审查，发现 42 项 → 验证后 6 个真问题 → 修复 5 项。

### 审查结果（详见 REVIEW_REPORT.md）

| 维度 | CRITICAL | HIGH | MEDIUM | LOW |
|------|----------|------|--------|-----|
| 安全 | 1 | 3 | 3 | 2 |
| 数据质量 | 5 | 5 | 7 | 3 |
| 前端契约 | 2 | 0 | 6 | 5 |

### 已修复（5 项，764 tests passed）

| # | 修复内容 | 改动文件 |
|---|----------|----------|
| C5 | 疼痛点字段发送：question SSE 事件包含 pain_point_type/severity | chat.py |
| C6 | SSE 错误处理：前端添加 error 事件分支，不再显示空白气泡 | ChatWindow.tsx |
| C1 | RAM 数据清洗：101 条文本 → 98 提取 + 3 NULL | phones.db |
| C2 | 电池数据清洗：121 条文本 → 120 提取 + 1 NULL | phones.db |
| C3 | 影像字段补全：26 款旗舰精确匹配 + 327 款品牌默认值 | phones.db |

### 假阳性（排除）

| 原始发现 | 原因 |
|----------|------|
| 3 个重复型号 | 数据库查询为 0，Agent 用了过时数据 |
| LLM 错误泄露 API 详情 | 已在 06-27 修复（commit 0a18172） |
| /health 信息泄露 | 已在 06-27 修复（60 秒缓存） |

### 不修复（经讨论确认）

| 问题 | 原因 |
|------|------|
| 品牌映射（小米/红米合并） | 分开是合理设计，合并反而丢失精度 |
| 中文 Prompt Injection | 正则误杀率太高，需 LLM 语义判断 |

### 新增文件

- `backend/data/clean_ram_battery.py` — RAM/电池数据清洗脚本
- `backend/data/fill_camera_fields.py` — 影像字段补全脚本
- `REVIEW_REPORT.md` — 完整审查报告（42 项发现）

---

## 2026-06-28 功能测试验证（TEST_CHECKLIST.md）

基于代码探索生成 266 个测试点的完整测试清单，启动项目进行实际验证。

### 测试结果

| 类别 | 测试数 | 通过 | 说明 |
|------|--------|------|------|
| 后端 API（curl） | 30 | 28 | 2 项为已知数据限制 |
| 前端界面（Playwright） | 8 | 8 | 核心交互全部通过 |

### 已验证功能

- API 基础端点：根路径、健康检查（含缓存）、手机列表/详情/过滤/分页
- Chat 接口：新会话、追问模式、推荐模式、对比模式、SSE 事件格式
- 多轮对话：完整追问流程、画像重置、否定需求处理、快捷回复交互
- 前端界面：欢迎页、消息显示、手机卡片、对比表格、搜索历史
- 安全：Prompt 注入防护（拒绝执行，不泄露系统提示词）

### 发现的数据质量问题（D1/D2 已在后续修复）

| # | 描述 | 严重程度 | 状态 |
|---|------|----------|------|
| D1 | RAM 字段含多余文字 | 低 | ✅ 已修复（2026-06-28 数据清洗） |
| D2 | 电池字段重复后缀 | 低 | ✅ 已修复（2026-06-28 数据清洗） |
| D3 | 努比亚小牛 RAM/存储/充电 null | 低 | — |
| D4 | 努比亚小牛重量 "5g"（明显错误） | 低 | — |
| D5 | 对比模式未匹配到用户指定型号 | 中 | — |
| D6 | camera_main 324 条缺失 | 低 | — |

详见 `TEST_CHECKLIST.md`（75 个关键测试点 + 预期结果 + 验证方式）。

---

## 2026-06-27 多维度审查修复（12 项，764+121 tests passed）

5 个并行审查 Agent（架构、安全、前端、API、测试）发现 110 项 → 验证后 13 项真实问题 → 修复 12 项（#8 跳过）

### 已修复

| # | 类别 | 修复内容 | 改动文件 |
|---|------|----------|----------|
| 1 | 架构 | SSE 生成器加 try/except，异常时返回 error 事件 | chat.py |
| 2 | 安全 | 系统提示词改用 system 角色，防止指令泄露 | intent.py, recommend.py |
| 3 | 安全 | /health 缓存 LLM 结果 60 秒，防止 API 额度耗尽 | main.py |
| 4 | 前端 | 6 个组件添加 ARIA 属性（无障碍） | InputBar, PhoneCard, QuickReplyButtons, MessageList, CompareTable, SearchHistory |
| 5 | 前端 | 添加加载指示器（三个脉冲点动画） | ChatWindow, MessageList, MessageItem |
| 6 | 测试 | `assert count == 353` 改为范围检查 `300-500` | test_data_completeness.py |
| 7 | 测试 | 创建 conftest.py 提取共享 fixtures | conftest.py, test_chat_route.py, test_chat_flow.py |
| 9 | API | 手机列表添加 offset 分页参数 | phones.py |
| 10 | API | SSE 错误格式添加 code 字段 | chat.py |
| 11 | 安全 | LLM 错误响应在生产环境隐藏 original_error | main.py |
| 12 | 数据 | 安兔兔 A18/A18 Pro 分数修正 | antutu_scores.json, test_antutu_config.py |
| 13 | 前端 | 消息 ID 改用 crypto.randomUUID() | ChatWindow.tsx |

### 跳过

| # | 原因 |
|---|------|
| 8 | threading.Lock → asyncio.Lock：锁操作微秒级，实际无性能影响；改动需修改 10+ 调用点和 10+ 测试文件，风险大于收益 |

### 验证修复

- 后端: 764 tests passed
- 前端: 121 tests passed
- 测试基础设施修复: rate limiter 双实例问题、health cache 测试隔离问题

---

## 已完成

| 阶段 | 内容 | 完成日期 |
|------|------|----------|
| MVP | 核心功能 9 个任务 | 2026-04-28 |
| 多轮对话 | 5 维度引导追问 + 痛点检测 | 2026-05-06 |
| 数据清洗 | 品牌修复 122 条、删除无效 51 条、RAM/Storage 补充 | 2026-05-02 |
| QA 测试 | 4 Agent 并行测试，5 问题全部修复 | 2026-05-05 |
| P3 改进 | LLM 上下文限制 + Token 估算 | 2026-05-02 |
| P0 改进 | 推荐解释增强 + 用户原话引用 + 潜在不足 | 2026-05-06 |
| P1 改进 | 体验标签库（19 特性 + 13 适用人群） | 2026-05-06 |
| P2 改进 | 痛点追问机制（6 种冲突检测） | 2026-05-06 |
| 安兔兔数据 | 处理器跑分配置化（JSON 文件） | 2026-05-06 |
| 代码审查 | ISSUE-027~031, 033, 035 修复 | 2026-06-25 |
| 测试覆盖 | 后端 chat 路由 16 测试 + 前端 7 组件 84 测试 | 2026-06-25 |
| 死代码清理 | 4 个未使用函数 + 23 个对应测试 | 2026-06-25 |
| 正则修复 | `_extract_budget` "X万以下" 匹配失败 | 2026-06-25 |
| 项目整理 | 23 个 backup DB 删除 + 19 个脚本移入 scripts/ | 2026-06-25 |
| 多维度审查 | 5 Agent 并行审查，42 项发现，验证 6 个真问题 | 2026-06-28 |
| 数据清洗 | RAM 98 条 + 电池 120 条提取，消除 TEXT 垃圾数据 | 2026-06-28 |
| 影像字段补全 | 26 款旗舰精确 + 327 款品牌默认 image_brand | 2026-06-28 |
| 疼痛点修复 | SSE question 事件发送 pain_point 字段，前端 UI 生效 | 2026-06-28 |
| SSE 错误处理 | 前端添加 error 事件分支，错误时显示提示 | 2026-06-28 |

---

## 关键决策记录

| 决策 | 选择 | 原因 | 日期 |
|------|------|------|------|
| LLM 模型 | DeepSeek Chat | 国内可用、性价比高 | 2026-04-28 |
| 流式通信 | SSE | 比 WebSocket 简单，FastAPI 原生支持 | 2026-04-28 |
| 会话存储 | 内存字典 + TTL | 简单可靠，单实例足够 | 2026-04-28 |
| 意图识别 | LLM + 规则兜底 | LLM 准确但可能失败，规则保底 | 2026-05-06 |
| 追问策略 | 5 维度 + 痛点检测 | 覆盖核心需求维度，冲突检测提升体验 | 2026-05-06 |

---

## 启动命令

```bash
# 后端（端口 8002）
cd "D:\my project\phone-pick-assistant"
.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8002

# 前端（端口 5173）
cd frontend
npm run dev

# 测试
.venv/Scripts/python.exe -m pytest tests/ -v
cd frontend && npm test
```

---

## 相关文档

- `README.md` — 项目说明、快速开始
- `docs/TODO-NEXT.md` — 后续待办
- `docs/FORMAL_VERSION_PLAN.md` — 正式版计划
- `issues/` — 问题追踪（ISSUE-001 ~ ISSUE-035）
