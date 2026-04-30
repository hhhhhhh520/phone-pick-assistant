# 手机选购助手 - 代码审查问题修复记录

> 创建时间: 2026-04-29
> 状态: 🟢 已解决

## 问题描述

代码审查发现 5 个 Blocker 级别问题需要修复。

## 修复内容

### 1. 会话服务并发安全问题 ✅
**文件**: `backend/services/session.py`

**问题**: 使用模块级全局字典存储会话，多线程/多进程环境下存在竞态条件。

**解决方案**:
- 添加 `threading.Lock` 保护所有读写操作
- 所有访问 `sessions` 字典的操作都在 `with _sessions_lock:` 块内执行

---

### 2. 会话存储内存泄漏 ✅
**文件**: `backend/services/session.py`, `backend/main.py`

**问题**: 会话创建后永不清理，长期运行内存持续增长。

**解决方案**:
- 会话存储改为 `Dict[str, Tuple[List[Dict], datetime]]`，记录最后活动时间
- 添加 `SESSION_EXPIRE_MINUTES = 30` 配置，30分钟不活跃自动过期
- 添加 `cleanup_expired_sessions()` 方法清理过期会话
- 在 `main.py` 添加后台任务，每5分钟自动清理

---

### 3. LLM服务缺少HTTP错误处理 ✅
**文件**: `backend/services/llm.py`

**问题**: `chat_stream` 方法未检查 `response.status_code`，API 返回 4xx/5xx 错误时无法正确处理。

**解决方案**:
- 添加 `LLMError` 异常类
- 检查 `response.status_code != 200` 时读取错误内容并抛出异常
- 添加日志记录

---

### 4. 意图识别降级处理不当 ✅
**文件**: `backend/services/intent.py`

**问题**: JSON 解析失败时返回默认 IntentResult，丢失用户输入的预算、品牌等关键信息。

**解决方案**:
- 添加 `_fallback_intent_recognition()` 基于规则的降级识别
- 添加 `_extract_json_from_response()` 从响应中提取JSON
- 解析失败时记录原始响应并使用降级策略

---

### 5. phones.py 统计逻辑问题 ✅
**文件**: `backend/api/routes/phones.py`

**问题**: `total` 计算逻辑混淆（先limit再count），且缺少输入参数验证。

**解决方案**:
- 修正为 `total = query.count()` 在 `limit` 之前
- 使用 FastAPI `Query` 添加参数验证：
  - `min_price`, `max_price`: `ge=0`
  - `limit`: `ge=1, le=100`

---

## 相关文件

- `backend/services/session.py` - 会话服务
- `backend/services/llm.py` - LLM服务
- `backend/services/intent.py` - 意图识别服务
- `backend/api/routes/phones.py` - 手机列表API
- `backend/main.py` - 应用入口

## 修复验证

所有修改已通过代码审查，建议运行测试验证功能正常。
