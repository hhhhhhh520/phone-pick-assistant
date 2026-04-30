# 手机选购助手 - 后续待办事项

> 创建时间: 2026-04-28
> 状态: 待执行

---

## 当前状态

**正式版 4 个功能已实现完成**：
- ✅ Task 1: 搜索历史
- ✅ Task 2: 手机图片
- ✅ Task 3: 对比表格
- ✅ Task 4: 多轮对话

---

## 待办事项

### 1. 最终验证测试

启动服务并测试所有功能：

```bash
# 启动后端
cd "D:\my project\phone-pick-assistant"
python -m uvicorn backend.main:app --reload --port 8002

# 启动前端（另一个终端）
cd "D:\my project\phone-pick-assistant\frontend"
npm run dev
```

**验证清单**：
- [ ] 搜索历史：发起多次对话，历史正确显示，点击可恢复
- [ ] 手机图片：手机卡片显示图片，加载失败显示占位符
- [ ] 对比表格：输入"对比小米14和华为P60"，表格正确显示，差异高亮
- [ ] 多轮对话：问"推荐3000元手机"→追问"有没有便宜点的"→系统理解上下文

### 2. 生产环境改进（Task 4 代码审查发现）

**Important 问题**（非阻塞，但上线前需处理）：

1. **Session 内存泄漏** - `backend/services/session.py`
   - 问题：sessions 永不过期，会导致内存泄漏
   - 解决：添加 TTL 过期机制

2. **LLM 历史上下文无限制** - `backend/services/recommend.py`
   - 问题：历史消息可能超出 token 限制
   - 解决：限制传入 LLM 的历史消息数量（如最近 6 条）

3. **全局 sessions 竞态条件** - `backend/services/session.py`
   - 问题：并发请求可能导致数据不一致
   - 解决：使用 `threading.Lock` 或迁移到 Redis

### 3. Task 5: 价格实时性（暂不实现）

待正式上线后再考虑：
- 数据源调研（京东API/爬虫/手动更新）
- 定时任务设计
- 价格变动日志

### 4. 其他改进建议

**Task 2 手机图片**：
- 当前使用占位图，后续需收集真实手机图片 URL

**Task 3 对比表格**：
- 可考虑添加屏幕类型（screen.type）的高亮对比

---

## 文件路径

- 设计文档：`docs/superpowers/specs/2026-04-28-formal-version-design.md`
- 实现计划：`docs/superpowers/plans/2026-04-28-formal-version-implementation.md`
- 项目进度：`PROGRESS.md`

---

## Git 提交记录

```
e1fc689 docs: 更新项目进度，完成正式版4个功能
64e4dd3 fix: 添加屏幕行的高亮逻辑
184fe2e feat: 添加手机图片展示功能
1f1fc6c feat: 添加搜索历史功能
```
