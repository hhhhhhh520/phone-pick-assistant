# 手机列表与详情接口字段契约不一致
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

三个序列化路径返回的手机字段不统一，前端拿不到一致的数据：

| 接口 | 返回字段 | 字段数 |
|------|----------|--------|
| `GET /api/phones`（列表） | `id, brand, model, price` | 4 |
| `GET /api/phones/{id}`（详情） | 含 `release_date, screen, processor, ...imageUrl, cameraScoring` | 20 |
| `POST /api/chat` 的 `phones` 事件 | `to_dict()` 输出（另一套） | — |

## 出现原因

- 列表接口（`phones.py`）手动 select 了 4 个字段，没复用 `Phone.to_dict()`
- 详情接口复用 `to_dict()`，返回 20 字段
- 字段命名风格混乱：`release_date`（snake_case）与 `imageUrl`（camelCase）与 `cameraScoring`（PascalCase）三种风格共存

## 影响

前端 `PhoneCard` 组件依赖 `phone.imageUrl`，但**列表接口根本不返回 imageUrl 字段** → 列表页图片全部走默认图标占位（与 ISSUE-040 叠加，图片问题更严重）。只有 chat 推送的 phones 事件带的卡片才有图片。

## 解决方案

1. 列表接口复用 `to_dict()` 或显式补充 `imageUrl` 等前端需要的字段
2. 统一字段命名风格（建议全 snake_case 或全 camelCase，用 Pydantic response_model 约束）
3. 三套序列化路径统一用一个 schema

## 相关文件

- `backend/api/routes/phones.py`（列表查询字段）
- `backend/models/domain.py`（`Phone.to_dict`）
- `frontend/src/components/PhoneCard.tsx`（依赖 `phone.imageUrl`）

## 参考资料

- 实测：2026-07-02 curl 对比列表/详情接口字段
