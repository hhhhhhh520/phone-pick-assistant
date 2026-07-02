# CLAUDE.md — 手机选购助手

## 项目结构

```
backend/                # FastAPI 后端
├── main.py             # 入口 + CORS + 生命周期
├── config.py           # Settings (pydantic-settings)
├── api/routes/chat.py  # 核心聊天路由（SSE 流式）
├── api/routes/phones.py # 手机列表/详情 API
├── api/dependencies.py # 服务单例（DI）
├── models/domain.py    # SQLAlchemy ORM + AnTuTu 跑分
├── models/schemas.py   # Pydantic 模型（IntentResult, UserProfile）
├── services/           # 业务逻辑层
│   ├── intent.py       # LLM 意图识别 + 规则兜底
│   ├── recommend.py    # LLM 推荐生成（SSE 流式）
│   ├── retrieval.py    # 数据库检索 + 场景排序
│   ├── session.py      # 内存会话管理（TTL 30min）
│   ├── llm.py          # DeepSeek API 客户端
│   ├── question.py     # 追问生成 + 痛点检测
│   └── model_parser.py # 推荐型号解析
├── utils/security.py   # Prompt 注入防护 + XSS 防御
└── data/phones.db      # SQLite（353 款手机/17 品牌）
frontend/               # React 19 + Vite + TailwindCSS
scripts/                # 数据处理/爬取工具脚本（非核心应用）
tests/                  # pytest（778 passed）
```

## 关键命令

```bash
# 后端
.venv/Scripts/python.exe -m uvicorn backend.main:app --port 8002

# 前端
cd frontend && npm run dev

# 测试
.venv/Scripts/python.exe -m pytest tests/ -v
cd frontend && npm test

# 前端构建
cd frontend && npm run build
```

## 架构要点

- **推荐流水线**: 意图识别 → 需求画像 → 完整性检查 → 分级回退检索 → LLM 推荐
- **SSE 事件流**: session → intent → (notice) → question/phones → content → done
- **分级回退检索** (`retrieval.search_with_fallback`): tier-1 全过滤 → tier-2 放宽场景但保留预算+品牌+场景排序 → tier-3 空结果+告警。**禁止回退到 `get_all_phones` 丢预算**（ISSUE-036）
- **对比型号找不到**: 发 `notice` 事件提示，**不调 `compare([])`** 避免 LLM 幻觉（ISSUE-039）
- **会话管理**: 内存字典 + threading.Lock，TTL 30 分钟，后台清理 5 分钟
- **LLM 调用**: DeepSeek Chat，流式输出，规则兜底（LLM 失败时）
- **/health**: LLM 状态由后台任务异步刷新（60s），请求读 `_llm_health` 缓存不阻塞，HTTP 永远 200（ISSUE-042）
- **场景排序**: 游戏→AnTuTu 跑分、拍照→主摄+影像品牌、续航→电池容量

## 开发规范

- 测试通过不代表功能正常，必须运行端到端测试验证实际功能
- 修改代码前先存档：`git add . && git commit -m "chore: 存档 - [描述]"`
- 每次修改必须新增针对性测试
- 发现报错立即修复，不允许跳过或忽略

## 已知限制

- SQLite 单文件数据库，不适合高并发
- 会话存储在内存中，重启丢失
- LLM 依赖 DeepSeek API，需要网络连接

## 相关文档

- `README.md` — 快速开始、功能说明
- `PROGRESS.md` — 项目进度、已完成事项
- `docs/TODO-NEXT.md` — 后续待办
- `issues/` — 问题追踪（ISSUE-001 ~ ISSUE-045）
