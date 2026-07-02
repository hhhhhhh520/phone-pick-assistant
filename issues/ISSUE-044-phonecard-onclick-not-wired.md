# PhoneCard onClick未接线，点击卡片无反应
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

手机卡片（PhoneCard）渲染为 `role="button"` + `tabIndex=0`，暗示可点击交互，但实际点击无任何反应——无详情弹窗、无展开、无跳转。

## 出现原因

- `PhoneCard.tsx` 定义了 `onClick` prop 并实现了点击/键盘交互（第 104-110 行）
- 但 `MessageItem.tsx:99` 渲染时 **未传入 onClick**：`<PhoneCard key={phone.id} phone={phone} />`
- onClick 始终为 undefined，点击空操作

## 影响

- 用户点击手机卡片期望查看详情，却毫无反馈，体验断裂
- 符合 CLAUDE.md "功能完整性"规则禁止的"设计了但未集成的功能"——组件有完整交互代码但从未接线

## 解决方案

任选其一：
1. **接线详情**：MessageItem 传入 onClick → 弹窗展示 `/api/phones/{id}` 详情（含 cameraScoring 等 20 字段）
2. **去除交互伪装**：若暂不实现详情，去掉 role=button/tabIndex/onKeyDown，避免误导用户和辅助技术
3. 跳转外链（phone.url 来源页）

推荐方案1，详情接口已存在且数据完整。

## 相关文件

- `frontend/src/components/PhoneCard.tsx:88-125`（onClick 定义）
- `frontend/src/components/MessageItem.tsx:99`（未传 onClick）

## 参考资料

- 实测：2026-07-02 点击卡片无弹窗
- CLAUDE.md 功能完整性规则
