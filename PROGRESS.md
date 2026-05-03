# 手机选购助手 - 开发进度

> 创建时间: 2026-04-28 | 最后更新: 2026-05-02

## 项目概述
**项目地址**: D:\my project\phone-pick-assistant
**技术栈**: FastAPI + React + DeepSeek API + SQLite
**当前状态**: 正式版功能开发中

---

## 当前进度

### ✅ 已完成
| 阶段 | 内容 | 完成日期 |
|------|------|----------|
| MVP | 9个任务全部完成 | 2026-04-28 |
| Task 1 | 搜索历史 | 2026-04-28 |
| Task 2 | 手机图片 | 2026-04-28 |
| Task 3 | 对比表格 | 2026-04-28 |
| Task 4 | 多轮对话 | 2026-04-28 |
| Bug修复 | 多轮对话意图识别问题 | 2026-04-30 |
| Bug修复 | 对比功能型号匹配问题 | 2026-05-01 |
| ISSUE-006 | 服务实例化不一致 | 2026-05-01 |
| ISSUE-010 | 请求取消机制（AbortController） | 2026-05-02 |
| ISSUE-013 | Prompt注入防护 | 2026-05-02 |
| ISSUE-016 | 日志记录 | 2026-05-02 |
| ISSUE-020 | Error Boundary | 2026-05-02 |
| Session内存泄漏 | TTL过期机制 + 统计端点 | 2026-05-02 |
| P3 | LLM历史上下文限制 | 2026-05-02 |
| P4 | 收集真实手机图片URL | 2026-05-02 |
| 上线阻塞项 | CORS配置+健康检查+错误处理+输入验证 | 2026-05-02 |

### ⏳ 进行中
| 任务 | 状态 | 问题 |
|------|------|------|
| - | - | - |

### 📋 待办
| 优先级 | 任务 | 说明 |
|--------|------|------|
| P6 | 补充processor数据 | 286条缺失，无法从型号提取，需外部数据源 |
| P7 | 补充camera_main数据 | 324条缺失，需外部数据源 |

---

## 2026-05-02 数据清洗记录

### 数据清洗内容

**1. 修复品牌错乱 (122条)**
- 问题：品牌字段与型号不匹配，如"荣耀 真我GT6"
- 修复：从型号名称检测正确品牌并更新
- 结果：品牌分布更准确

**2. 删除无效记录 (51条)**
- 删除价格=0的记录（未上市机型、爬取失败等）
- 删除后剩余556条有效记录

**3. 补充RAM/Storage参数**
- 从型号名称提取RAM和Storage
- 处理中文括号（）、英文括号()、TB/GB单位
- RAM: 49.3% → 92.6%
- Storage: 51.6% → 97.1%

### 数据完整性对比

| 字段 | 清洗前 | 清洗后 | 变化 |
|------|--------|--------|------|
| 总记录 | 607 | 556 | -51 |
| 品牌 | 100% | 100% | - |
| 价格 | 91.6% | 100% | +8.4% |
| 存储 | 51.6% | 97.1% | +45.5% |
| 内存 | 49.3% | 92.6% | +43.3% |
| 处理器 | 50.2% | 48.6% | -1.6% |
| 主摄 | 42.8% | 41.7% | -1.1% |
| 图片 | 94.2% | 93.7% | -0.5% |

### 品牌分布（清洗后）

小米74款、vivo73款、华为61款、真我52款、OPPO50款、苹果48款、三星40款、一加33款...共15个品牌

---

## 2026-05-02 修改记录（P3+P4任务）

### P3: LLM历史上下文限制

**实现内容**：
1. `backend/config.py` - 添加上下文配置项
   - max_context_messages=10（传入LLM最大消息数）
   - max_context_tokens=4000（上下文最大token数）
   - max_message_length=500（单条消息最大字符数）

2. `backend/services/llm.py` - 添加token估算和消息截断函数
   - estimate_tokens(): 基于字符数估算token
   - truncate_messages(): 按配置截断消息列表，保留系统消息

3. `backend/services/recommend.py` - 使用统一上下文管理
   - recommend()和compare()方法调用truncate_messages()

4. `backend/services/intent.py` - 移除重复截断逻辑
   - 使用llm.py提供的统一方法

5. `backend/services/session.py` - 存储层配置
   - MAX_STORED_MESSAGES=50（保留完整历史用于追溯）

### P4: 收集真实手机图片URL

**实现内容**：
1. 整理60款手机型号清单（12个品牌）

2. `backend/data/phone_images.json` - 图片URL映射文件
   - 11款官方URL（Apple 7款 + 三星 4款）
   - 31款本地图片路径
   - 18款无图片（待补充）

3. `backend/data/image_loader.py` - 图片映射加载器
   - get_image_url(): 获取手机图片URL
   - get_image_source(): 获取图片来源类型
   - get_statistics(): 获取映射统计

4. `backend/data/update_images.py` - 数据库迁移脚本
   - 支持 --dry-run 预览模式
   - 更新数据库image_url字段

5. `frontend/src/components/PhoneCard.tsx` - 图片降级处理
   - 添加DefaultPhoneIcon组件
   - 图片加载失败时显示默认图标

### 测试覆盖

- `tests/test_llm_context.py` - 18个测试（token估算、消息截断）
- `tests/test_image_loader.py` - 28个测试（图片加载器）
- 全部96个测试通过

---

## 2026-04-30 修改记录

### 修复：多轮对话意图识别问题

**问题**：用户追问"有没有便宜点的"时，系统无法理解上下文，返回价格=0的手机

**根本原因**：
1. `IntentService.recognize()` 方法没有接收历史消息参数
2. `RetrievalService.search()` 没有过滤 price=0 的无效数据
3. 数据库中有43条 price=0 的手机记录，且有图片，排序时排在前面

**修复内容**：
1. `backend/services/intent.py` - 添加 `history` 参数，支持多轮对话上下文
2. `backend/services/retrieval.py` - 所有方法添加 `Phone.price > 0` 过滤
3. `backend/api/routes/chat.py` - 传入历史消息给意图识别

**验证结果**：
- 第一轮："推荐3000元手机" → 返回 2549-2598 元
- 第二轮："有没有便宜点的" → 返回 1049-1160 元 ✅

### 进行中：对比功能型号匹配

**问题**：用户输入"对比小米14和华为P60"，返回错误的手机

**根本原因**：
1. 型号匹配逻辑 `Phone.model.contains(model)` 过于简单
2. "小米14" 提取核心词 "14" 后，匹配到 "Redmi Note 14"
3. 需要更智能的型号匹配逻辑

**当前状态**：已提交初步修复，但匹配逻辑仍需优化

---

## 2026-05-01 修改记录

### 修复：对比功能型号匹配问题

**问题**：用户输入"对比小米14和华为P60"，返回错误的手机（"小米14"匹配到"Redmi Note 14"）

**根本原因**：
1. `get_phones_by_model()` 去掉品牌名后只剩数字"14"
2. 数据库中所有小米系手机（含Redmi）品牌字段都是"小米"
3. `Phone.model.contains("14")` 匹配到"Redmi Note 14"

**修复方案**：三级匹配优先级
1. 精确匹配完整型号 `Phone.model == model`
2. 完整型号作为子串匹配 `Phone.model.contains(model)`
3. 提取核心型号但必须同品牌 `Phone.brand == brand_prefix AND Phone.model.contains(model_core)`

**验证结果**：
- "小米14" → 正确匹配"小米14"（之前错误匹配"Redmi Note 14"）
- "华为P60" → 匹配"P60 Pro"
- "Redmi Note 14" → 正确匹配
- 11个单元测试全部通过

---

## 2026-05-02 修改记录

### 新增：ISSUE-010 请求取消机制

**实现内容**：
1. `frontend/src/services/api.ts` - 添加 `abortCurrentRequest()` 函数
2. `frontend/src/components/InputBar.tsx` - 发送中显示取消按钮
3. `frontend/src/components/ChatWindow.tsx` - 处理取消逻辑和 AbortError

**效果**：用户可在请求过程中点击"取消"按钮中断请求

### 新增：ISSUE-013 Prompt注入防护

**实现内容**：
1. `backend/utils/security.py` - 安全工具模块
   - `sanitize_input()`: 清理用户输入，移除控制字符，HTML转义
   - `detect_injection_attempt()`: 检测15种注入攻击模式
   - `validate_chat_input()`: 验证聊天输入
   - `escape_for_prompt()`: 转义文本嵌入Prompt
2. `backend/api/routes/chat.py` - 集成输入验证
3. `tests/test_security.py` - 16个安全测试

**效果**：阻止Prompt注入攻击，保护系统指令

### 新增：ISSUE-016 日志记录

**实现内容**：
1. `backend/main.py` - 配置统一日志（控制台+文件）
2. `backend/services/session.py` - 添加会话操作日志
3. `backend/services/llm.py` - 添加LLM请求/响应日志

**效果**：便于调试和问题追踪

### 新增：ISSUE-020 Error Boundary

**实现内容**：
1. `frontend/src/components/ErrorBoundary.tsx` - 错误边界组件
2. `frontend/src/App.tsx` - 包裹根组件

**效果**：前端错误优雅降级，不白屏

### 新增：Session内存泄漏修复

**实现内容**：
1. 已有TTL过期机制（30分钟）
2. 已有定期清理任务（每5分钟）
3. 新增 `/stats/sessions` 端点监控内存使用

**效果**：防止长时间运行内存泄漏

---

## Git 提交记录

```
7c846d1 fix: 改进型号匹配逻辑，支持部分型号名称匹配
a1b2c3d fix: 修复多轮对话意图识别问题
```

---

## 启动命令

```bash
# 后端
cd "D:\my project\phone-pick-assistant"
.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8002

# 前端
cd frontend
npm run dev
```
