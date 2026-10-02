# 追问内部 code 泄漏到用户可见标题
> 创建时间: 2026-10-02 | 状态: 🟢已解决（含同批次 severity 徽标失效修复）

## 问题描述

2026-09-30 端到端实测（S4 预算800买拍照旗舰）发现追问卡片标题渲染为
"关于**brand_not_match_features**的追问"——后端内部 reason code 直接暴露给用户。

进一步核实：前端 `MessageItem.tsx` 的 `typeNames` 映射表只有 5 个旧语义键
（battery/storage/camera/performance/screen），而后端 `question.py`
`PAIN_POINT_TEMPLATES` 发出的 6 个 code 与其**零交集**，且兜底是
`|| message.painPointType`（透出原始值）——即当时**所有 6 种痛点追问的标题 100% 泄漏**，
不止实测看到的那一个。

## 出现原因

前后端类型枚举不同步：前端映射表停留在旧语义键，后端演进为 snake_case 模板键；
兜底分支选择了"透出原值"而非通用文案，使任何新增 code 都会直接暴露。

## 解决方案（2026-10-01 深夜开工，2026-10-02 完成）

1. `MessageItem.tsx` 的 `typeNames` 补全后端 PAIN_POINT_TEMPLATES 全集 6 键
   （预算不足/品牌与预算/游戏与拍照/续航与游戏/需求与预算/品牌与功能，语义对齐各模板 description），
   旧语义键保留（后端从未发出过，保留无害且有回归测试覆盖）
2. 兜底改为通用文案"偏好确认"——纵深防御：后端将来新增痛点类型也不会再泄漏内部 code
3. `types/index.ts:61` 字段注释同步（原注释只列旧 5 键）

**同批次修复（三路审查独立发现的同病灶）——severity 徽标从未渲染过**：
`severityColors/severityLabels` 只映射 `mild/moderate/severe`，而后端实际发出
`high/medium/low`（question.py 全部 return 点，backend 中 mild/moderate/severe 零命中），
`|| ''` 静默兜底使严重度徽标（轻度/中度/重点关注）恒为空、从不显示。修复：两表补
`high/medium/low` 键（旧键保留），`types` 注释同步。

**守卫测试**（`MessageItem.test.tsx` 新增 7 用例）：
code 泄漏 4（全 6 code **逐键断言专属标签**+反断言兜底替身 / 兜底 / 主场景 / 旧键回归）+
severity 3（后端实际枚举渲染 / 旧键 mild 回归 / 缺失不渲染）。先红 3 failed → 后绿 19。

> 注：测试内 `BACKEND_CODES`/`EXPECTED_LABELS` 是手抄副本（前端测试无法 import Python），
> 后端加键时需同步 `typeNames` 与测试列表——该同步靠人工，纵深由"未知 code 兜底"用例兜住。

**附带核查（无问题）**：模板占位符链路——唯二含 `{brand}/{min_price}/{feature}` 的分支
（brand_budget_conflict、brand_not_match_features）均有 `.format()` 且传参完整，
无花括号泄漏、无 KeyError 风险；其余分支所选模板不含占位符。

## 相关文件

- `frontend/src/components/MessageItem.tsx`（映射表 + 兜底）
- `frontend/src/test/MessageItem.test.tsx`（4 新用例）
- `frontend/src/types/index.ts:61-62`（注释同步：code 枚举 + severity 枚举）
- `backend/services/question.py`（只读参照：PAIN_POINT_TEMPLATES 6 键与发出点 451-527）
