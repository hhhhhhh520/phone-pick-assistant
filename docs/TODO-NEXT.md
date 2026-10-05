# 手机选购助手 - 后续待办事项

> 创建时间: 2026-04-28 | 更新时间: 2026-10-02
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

| 优先级 | 任务 | 当前缺口（2026-10-02 实测） | 说明 |
|--------|------|----------|------|
| P2 | sensor_main / telephoto_type | 351 款中 301 / 325 款缺 | 影像硬件数据，需外部数据源 |

> 注：processor / camera_main 已于数据补全批次填满（2026-10-02 实测空值为 0，
> 原"缺失 286/324 条"条目已过时移除）。

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

## 已修复（2026-07-02 ISSUE-036~045）

数据质量问题 D1~D5 已全部解决：
- D1/D2 RAM/电池字段清洗（2026-06-28）
- D3/D4 null 字段显示 + 重量错误：前端 CompareTable formatUnit 兜底显示 '-'（ISSUE-037）
- D5 对比型号匹配：missing 检测改子串回判，模糊命中不再误报（ISSUE-039）

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