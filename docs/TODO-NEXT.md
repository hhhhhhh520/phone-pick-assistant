# 手机选购助手 - 后续待办事项

> 创建时间: 2026-04-28 | 更新时间: 2026-05-05
> 状态: 正式版已完成

---

## 当前状态

**正式版功能已全部完成**：
- ✅ Task 1: 搜索历史
- ✅ Task 2: 手机图片
- ✅ Task 3: 对比表格
- ✅ Task 4: 多轮对话

**QA测试已通过**：
- 健康评分: 82/100
- 通过率: 89%
- 发现问题: 5个（全部已修复）

---

## 待办事项

### 1. 数据补充

| 优先级 | 任务 | 缺失数量 | 说明 |
|--------|------|----------|------|
| P6 | processor数据 | 286条 | 需外部数据源 |
| P7 | camera_main数据 | 324条 | 需外部数据源 |

### 2. Task 5: 价格实时性（暂不实现）

待正式上线后再考虑：
- 数据源调研（京东API/爬虫/手动更新）
- 定时任务设计
- 价格变动日志

### 3. 代码优化建议（非阻塞）

1. **chat.py 架构重构**（P2）
   - 120 行 `generate()` 函数拆分为 ChatOrchestrator
   - 详见 `issues/ISSUE-032`

---

## 启动命令

```bash
# 后端（端口8002）
cd "D:\my project\phone-pick-assistant"
.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8002

# 前端
cd frontend
npm run dev
```

---

## 相关文档

- 项目进度：`PROGRESS.md`
- 正式版计划：`docs/FORMAL_VERSION_PLAN.md`
- QA报告：`.gstack/qa-reports/qa-report-2026-05-05.md`