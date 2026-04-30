# 手机选购助手 - 正式版功能设计

> 创建时间: 2026-04-28
> 状态: 已确认

---

## 概述

本文档定义手机选购助手从 MVP 升级到正式版的5个功能设计。

**技术栈**: FastAPI + React + DeepSeek API + SQLite

**总预计时间**: 约9小时

---

## Task 1: 搜索历史

### 目标

用户可查看之前的搜索记录和推荐的手机，点击历史项可快速恢复对话。

### 设计决策

**存储内容**: 用户输入 + 推荐结果（方案2）

**存储位置**: localStorage（前端）

**数据结构**:
```typescript
interface SearchHistoryItem {
  id: string;
  query: string;           // 用户输入
  phones: Phone[];         // 推荐的手机列表
  timestamp: number;       // 时间戳
}
```

### 实现要点

1. 创建 `useSearchHistory` Hook
   - 使用 localStorage 存储
   - 提供添加、获取、清空方法
   - 最多保留20条历史

2. 创建 `SearchHistory.tsx` 组件
   - 展示历史列表（最近10条）
   - 点击历史项直接展示推荐结果，不重新请求
   - 清空历史按钮

3. 集成到 `ChatWindow.tsx`
   - 每次对话完成后保存历史
   - 在侧边栏或顶部展示历史组件

### 涉及文件

- `frontend/src/hooks/useSearchHistory.ts` (新建)
- `frontend/src/components/SearchHistory.tsx` (新建)
- `frontend/src/components/ChatWindow.tsx` (修改)

### 验证标准

- 发起多次对话后，历史记录正确显示
- 点击历史项可恢复之前的推荐结果
- 清空历史功能正常

---

## Task 2: 手机图片

### 目标

手机卡片展示真实图片，提升直观性。

### 设计决策

**图片来源**: 手动收集56款手机的京东/官网图片URL

**数据更新**: 在 seed.py 中添加 `image_url` 字段

### 实现要点

1. 后端模型更新
   - Phone 模型添加 `image_url` 字段
   - to_dict() 方法返回图片URL

2. 数据填充
   - 收集56款手机图片URL
   - 更新 seed.py 中的手机数据

3. 前端展示
   - PhoneCard 组件添加图片展示
   - 无图片时显示占位符

### 涉及文件

- `backend/models/domain.py` (修改，添加 image_url 字段)
- `backend/data/seed.py` (修改，填充图片URL)
- `frontend/src/components/PhoneCard.tsx` (修改，展示图片)
- `frontend/src/types/index.ts` (修改，添加 imageUrl 类型)

### 验证标准

- 手机卡片正确显示图片
- 无图片时显示占位符
- 图片加载失败时显示错误提示

---

## Task 3: 对比表格

### 目标

对比两款手机时，用表格清晰展示参数差异。

### 设计决策

**表格布局**: 纵向对比（方案B）
- 参数名在左列
- 手机A在中间列
- 手机B在右列
- 差异项高亮显示

### 实现要点

1. 前端组件
   - 创建 `CompareTable.tsx` 组件
   - 参数行：处理器、价格、内存、存储、电池、拍照、屏幕
   - 差异项用红色/黄色背景高亮

2. 后端逻辑
   - 对比意图返回结构化对比数据
   - 包含差异标记

3. 消息渲染
   - ChatMessage 组件识别对比消息
   - 渲染 CompareTable 组件

### 涉及文件

- `frontend/src/components/CompareTable.tsx` (新建)
- `frontend/src/components/MessageItem.tsx` (修改，渲染对比表格)
- `backend/services/recommend.py` (修改，对比逻辑)
- `backend/models/schemas.py` (修改，对比响应结构)

### 验证标准

- 对比两款手机时显示表格
- 差异项正确高亮
- 表格布局清晰易读

---

## Task 4: 多轮对话

### 目标

系统记住对话历史，支持追问。

### 设计决策

**存储位置**: 内存存储（后续正式上线可迁移到 Redis）

**会话管理**: session_id + 对话历史列表

### 实现要点

1. 后端会话管理
   - 创建 `SessionService` 类
   - 内存存储 session_id → messages 映射
   - 每个会话保留最近10轮对话

2. API修改
   - `/api/chat` 接口接收 `session_id`
   - 返回新 `session_id`（首次对话时生成）

3. LLM调用
   - 将历史消息作为上下文传入
   - 使用 DeepSeek API 的多轮对话能力

4. 前端集成
   - localStorage 存储 session_id
   - 每次请求携带 session_id

### 涉及文件

- `backend/services/session.py` (新建，会话管理)
- `backend/api/routes/chat.py` (修改，会话逻辑)
- `backend/services/llm.py` (修改，传入历史消息)
- `backend/models/schemas.py` (修改，添加 session_id)
- `frontend/src/services/api.ts` (修改，携带 session_id)
- `frontend/src/hooks/useSession.ts` (新建)

### 验证标准

- 用户问"推荐3000元的手机"
- 用户追问"有没有便宜点的"
- 系统理解上下文，推荐2000-2500元手机

---

## Task 5: 价格实时性

### 设计决策

**暂不实现**

理由：
- 价格实时性是"锦上添花"，不影响核心功能
- 爬虫有法律风险，京东API需要申请
- MVP阶段专注核心体验

后续正式上线时再考虑数据源方案。

---

## 执行顺序

```
Task 1 → Task 2 → Task 3 → Task 4
```

Task 5 暂不实现。

---

## 注意事项

1. 每个Task完成后运行测试验证
2. 每个Task完成后更新 PROGRESS.md
3. 遇到问题在 `issues/` 目录记录
4. Task 4 的内存存储设计要抽象好，便于后续迁移