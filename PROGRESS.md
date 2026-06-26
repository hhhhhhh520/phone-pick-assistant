# 手机选购助手 - 项目进度

> 创建时间: 2026-04-28 | 最后更新: 2026-06-25（含正则修复+脚本整理）

## 项目概述

**项目地址**: D:\my project\phone-pick-assistant
**技术栈**: FastAPI + React 19 + DeepSeek API + SQLite
**当前状态**: 功能完成，代码质量优化中

---

## 当前待办

| 优先级 | 任务 | 说明 | 相关 Issue |
|--------|------|------|-----------|
| P2 | chat.py 架构重构 | 120 行业务逻辑拆分为 ChatOrchestrator | ISSUE-032 |
| P6 | 补充 processor 数据 | 286 条缺失，需外部数据源 | — |
| P7 | 补充 camera_main 数据 | 324 条缺失，需外部数据源 | — |

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
