# ISSUE-006 服务实例化不一致

> 创建时间: 2026-05-01
> 状态: 🟢 已解决

## 问题描述

`session_service` 是模块级实例，但 `intent_service`、`retrieval_service`、`recommend_service` 每次请求创建新实例。实例化策略不一致，难以理解设计意图。

**位置**: `backend/api/routes/chat.py:14-25`

## 出现原因

开发时没有统一的服务生命周期管理策略，不同服务采用了不同的实例化方式。

## 解决方案

统一使用 FastAPI 依赖注入模式：

1. 在 `dependencies.py` 添加服务获取函数：
   - `get_session_service()` - 单例
   - `get_intent_service()` - 单例
   - `get_recommend_service()` - 单例

2. 在 `chat.py` 使用 `Depends()` 注入服务：
   ```python
   @router.post("")
   async def chat(
       request: ChatRequest,
       db: Session = Depends(get_db),
       session_service: SessionService = Depends(get_session_service),
       intent_service: IntentService = Depends(get_intent_service),
       recommend_service: RecommendService = Depends(get_recommend_service)
   ):
   ```

3. `RetrievalService` 需要数据库连接，保持每次请求创建（通过 `get_db` 依赖）

## 相关文件

- `backend/api/dependencies.py` - 新增服务依赖函数
- `backend/api/routes/chat.py` - 使用依赖注入

## 验证结果

- 导入测试通过
- 所有服务通过依赖注入获取
- 实例化策略统一