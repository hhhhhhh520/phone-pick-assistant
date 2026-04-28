# CORS 跨域请求失败

> 创建时间: 2026-04-28
> 状态: 🟢 已解决

## 问题描述

前端访问后端 API 时报错：
```
Access to fetch at 'http://localhost:8001/api/chat' from origin 'http://localhost:5179' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 出现原因

**根本原因**：多个问题叠加

1. **TypeScript `verbatimModuleSyntax: true`** - 类型导入必须用 `import type { X }`，否则报模块导出错误
2. **FastAPI CORS 配置冲突** - `allow_origins=["*"]` 和 `allow_credentials=True` 不能同时使用，导致 CORS 头不返回
3. **端口冲突** - 旧进程残留占用端口，新启动的进程配置没生效
4. **localhost vs 127.0.0.1** - 浏览器视为不同的源，前端用 localhost，后端绑定 127.0.0.1 导致跨域

## 解决方案

1. 类型导入改为 `import type { X } from '../types'`
2. CORS 配置改为列出具体端口：
   ```python
   allow_origins=["http://localhost:5173", "http://localhost:5174", ...],
   allow_credentials=True,
   ```
3. 杀掉旧进程，换新端口启动
4. 前后端统一使用 `localhost`

## 相关文件
- `backend/main.py` - CORS 配置
- `frontend/src/services/api.ts` - API 地址
- `frontend/src/components/*.tsx` - 类型导入

## 参考资料
- [FastAPI CORS 文档](https://fastapi.tiangolo.com/tutorial/middleware/)
- [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
