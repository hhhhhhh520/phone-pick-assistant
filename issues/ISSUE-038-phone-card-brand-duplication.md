# 手机卡片品牌名重复显示
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

推荐卡片标题显示"努比亚 努比亚小牛""华为 华为畅享 80"——brand 和 model 拼接时，model 字段本身已包含品牌名，导致品牌重复。

## 出现原因

前端 PhoneCard 组件渲染 `brand + model`，但数据库 `model` 字段存的是"努比亚小牛""华为畅享 80"（已含品牌），`brand` 字段又存"努比亚""华为"。

## 解决方案

前端拼接时去重，或后端 `to_dict` 返回 `display_name` 字段统一处理；也可数据层让 model 只存纯型号（如"小牛""畅享 80"）。

## 相关文件

- `frontend/src/components/PhoneCard.tsx`
- `backend/models/domain.py`

## 参考资料

- 实测：2026-07-02 无头浏览器测试发现
