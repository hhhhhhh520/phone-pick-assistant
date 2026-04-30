# 手机选购助手 - 正式版改进计划

> 创建时间: 2026-04-28
> 目标: 从MVP升级到正式可用版本

---

## Task 1: 搜索历史

**难度**: ⭐ | **预计时间**: 1小时

**目标**: 用户可以查看之前的搜索记录和推荐的手机

**实现步骤**:
- [ ] 前端：创建 `useSearchHistory` Hook，使用 localStorage 存储历史
- [ ] 前端：创建 `SearchHistory.tsx` 组件，展示历史列表
- [ ] 前端：点击历史项可快速发起相同查询
- [ ] 前端：添加清空历史按钮

**涉及文件**:
- `frontend/src/hooks/useSearchHistory.ts` (新建)
- `frontend/src/components/SearchHistory.tsx` (新建)
- `frontend/src/components/ChatWindow.tsx` (修改，集成历史组件)

**验证**: 发起多次对话后，历史记录正确显示，点击可复现查询

---

## Task 2: 手机图片

**难度**: ⭐⭐ | **预计时间**: 2小时

**目标**: 手机卡片展示真实图片，提升直观性

**实现步骤**:
- [ ] 数据：为手机数据添加 `image_url` 字段
- [ ] 数据：收集56款手机的官方图片URL（可用京东/官网图片）
- [ ] 后端：更新 `Phone` 模型，添加 `image_url` 字段
- [ ] 后端：更新 seed.py，填充图片URL
- [ ] 前端：修改 `PhoneCard.tsx`，展示手机图片

**涉及文件**:
- `backend/models/domain.py` (修改，添加字段)
- `backend/data/seed.py` (修改，添加图片URL)
- `frontend/src/components/PhoneCard.tsx` (修改，展示图片)
- `frontend/src/types/index.ts` (修改，添加类型)

**验证**: 手机卡片正确显示图片，无图片时显示占位符

---

## Task 3: 对比表格

**难度**: ⭐⭐ | **预计时间**: 2小时

**目标**: 对比两款手机时，用表格清晰展示参数差异

**实现步骤**:
- [ ] 前端：创建 `CompareTable.tsx` 组件
- [ ] 前端：设计表格布局（参数名 | 手机A | 手机B）
- [ ] 前端：高亮差异项（如价格、处理器不同时标红）
- [ ] 后端：修改推荐服务，对比意图返回结构化对比数据
- [ ] 前端：集成到聊天消息展示中

**涉及文件**:
- `frontend/src/components/CompareTable.tsx` (新建)
- `frontend/src/components/ChatMessage.tsx` (修改，渲染对比表格)
- `backend/services/recommend.py` (修改，对比逻辑)
- `backend/models/schemas.py` (修改，对比响应结构)

**验证**: 对比两款手机时显示表格，差异项正确高亮

---

## Task 4: 多轮对话上下文

**难度**: ⭐⭐⭐ | **预计时间**: 4小时

**目标**: 系统记住对话历史，支持追问

**实现步骤**:
- [ ] 后端：设计会话管理机制（内存存储或Redis）
- [ ] 后端：创建 `session_id` 生成和管理
- [ ] 后端：修改 `/api/chat` 接口，接收 `session_id`
- [ ] 后端：存储每个会话的对话历史（最近10轮）
- [ ] 后端：修改LLM调用，将历史消息作为上下文传入
- [ ] 前端：生成并存储 `session_id`（localStorage）
- [ ] 前端：每次请求携带 `session_id`

**涉及文件**:
- `backend/services/session.py` (新建，会话管理)
- `backend/api/routes/chat.py` (修改，会话逻辑)
- `backend/services/llm.py` (修改，传入历史消息)
- `frontend/src/services/api.ts` (修改，携带session_id)
- `frontend/src/hooks/useSession.ts` (新建)

**验证**:
- 用户问"推荐3000元的手机"
- 用户追问"有没有便宜点的"
- 系统理解上下文，推荐2000-2500元手机

---

## Task 5: 价格实时性

**难度**: ⭐⭐⭐⭐ | **预计时间**: 需要研究

**目标**: 手机价格定期更新，保持准确性

**实现步骤**:
- [ ] 调研：确定数据源（京东API/官网爬虫/手动更新）
- [ ] 后端：创建价格更新脚本
- [ ] 后端：添加定时任务（每周更新）
- [ ] 后端：添加价格变动日志
- [ ] 前端：显示价格更新时间

**涉及文件**:
- `backend/services/price_updater.py` (新建)
- `backend/models/domain.py` (修改，添加价格更新时间字段)
- `frontend/src/components/PhoneCard.tsx` (修改，显示更新时间)

**验证**: 运行更新脚本后，价格正确更新

---

## 执行顺序

```
Task 1 (搜索历史) → Task 2 (手机图片) → Task 3 (对比表格) → Task 4 (多轮对话) → Task 5 (价格实时性)
```

## 注意事项

1. 每个Task完成后运行测试验证
2. 每个Task完成后更新 PROGRESS.md
3. 遇到问题在 `issues/` 目录记录
4. Task 5 需要先调研数据源可行性
