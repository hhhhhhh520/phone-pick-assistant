# 手机列表API排序参数未实现
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

`GET /api/phones` 传入 `sort=price_asc` 和 `sort=price_desc` 返回顺序完全一致（Find N 5999 / Find N3 Flip 6799 / Find X 5999），排序未生效，且默认结果也无序（5999→6799→5999 既非升序也非降序）。

## 出现原因

`backend/api/routes/phones.py` 的 `list_phones` 函数**未定义 `sort` 查询参数**，传入的 sort 被 FastAPI 静默丢弃。查询无 `order_by`，按数据库自然顺序返回（无序）。

## 影响

- 用户无法按价格排序浏览手机列表
- 无效 sort 参数返回 200 而非 422，未校验（用户以为排序生效，实际没生效）

## 解决方案

1. 在路由增加 `sort: str = Query(None)` 参数，支持 `price_asc`/`price_desc` 等枚举
2. 对应添加 `query.order_by(Phone.price.asc()/desc())`
3. 无效 sort 值返回 422 或忽略并返回默认顺序（需明确策略）

## 相关文件

- `backend/api/routes/phones.py:11-37`

## 参考资料

- 实测：2026-07-02 curl 验证 sort 参数无效
