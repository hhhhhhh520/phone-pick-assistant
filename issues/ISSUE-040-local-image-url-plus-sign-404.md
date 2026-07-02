# 本地图片URL含+号导致43款机型图片404
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

数据库中 43 款机型的 `image_url` 是本地相对路径 `/images/xxx.png`（OPPO 9、vivo 10、华为 6、小米 15、三星 2、荣耀 1），其中含 `+` 号的文件名（如 `OPPO Reno15 Pro(12GB+256GB)_1.jpg`）在浏览器加载时 404，用户只能看到默认图标占位，看不到真机图。

## 出现原因

1. 后端 `main.py:72-74` 挂载 `/images` 静态目录到项目根 `images/` 文件夹（292 个文件实际存在）
2. 前端 `PhoneCard.tsx:92-98` `getFullImageUrl` 把 `/images/xxx.png` 拼成 `http://localhost:8002/images/xxx.png`，**未做 URL 编码**
3. 文件名含 `+`（如 `12GB+256GB`）时，浏览器请求中 `+` 被当作空格 → 文件名不匹配 → 404
4. 触发 `<img onError>` 回退到 `DefaultPhoneIcon`（默认图标）

验证（curl 实测）：
- `+` 不编码 → HTTP 000（失败）
- `+` 编码为 `%2B` → **HTTP 200**（成功）

## 影响

43 款用本地路径的机型中，文件名含 `+` 的（存储配置标注如 `12GB+256GB`）图片无法显示，降级为默认图标。远程 http URL（170 款，中关村在线图床）不受影响。

## 解决方案

任选其一：
1. **前端编码**：`getFullImageUrl` 对本地路径做 `encodeURI`，特别注意 `+` → `%2B`
2. **数据层重命名**：把 images/ 目录文件名和数据库 URL 中的 `+` 替换为 `_` 或去掉
3. **后端中间件**：静态文件服务对 `+` 做兼容处理

推荐方案1（前端一行改动，影响最小）。

## 相关文件

- `frontend/src/components/PhoneCard.tsx:92-98`（`getFullImageUrl`）
- `backend/main.py:72-74`（静态文件挂载）
- `backend/data/phones.db`（image_url 字段）

## 参考资料

- README 称图片覆盖 93.7%，但实际可访问率因 + 号问题低于此值
- 实测：2026-07-02 无头浏览器 + curl 验证
