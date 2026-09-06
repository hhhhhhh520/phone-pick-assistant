# 手机选购助手

AI对话式手机选购助手，支持需求推荐、参数对比、预算筛选三种场景。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite + LLM API（OpenAI/Anthropic 双协议，当前接入火山方舟）
- **前端**: React 19 + Vite + TailwindCSS + TypeScript
- **通信**: SSE流式输出

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 后端启动

```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY（支持 DeepSeek 或火山方舟，见 .env.example 注释）

# 初始化数据库
python -m backend.data.seed

# 启动服务（端口8002）
uvicorn backend.main:app --reload --port 8002
```

### 前端启动

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev
```

访问 http://localhost:5173

## 功能特性

### 核心功能

- **智能推荐**: 根据用户需求推荐合适的手机，支持多轮对话追问
- **参数对比**: 对比两款手机的各项参数，差异高亮显示
- **预算筛选**: 按价格区间筛选手机
- **流式输出**: SSE实时显示AI回复
- **加载指示器**: 流式生成时显示脉冲点动画
- **搜索历史**: localStorage存储历史记录，一键恢复
- **无障碍**: ARIA标签支持屏幕阅读器

### 安全特性

- **Prompt注入防护**: 检测20+危险模式，拦截恶意输入
- **XSS防护**: HTML转义处理
- **SQL注入防护**: ORM参数化查询
- **Rate Limiting**: 20次/分钟请求限制
- **输入验证**: 长度限制、空值验证、特殊字符过滤

### 性能指标

- 50并发100%成功率
- 平均响应时间 ~200ms
- 会话TTL过期机制（30分钟）

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 对话接口(SSE)，限流20/min |
| `/api/phones` | GET | 手机列表，支持品牌/价格过滤、offset分页、sort排序(price_asc/price_desc) |
| `/api/phones/{id}` | GET | 手机详情 |
| `/health` | GET | 健康检查 |
| `/stats/sessions` | GET | 会话统计 |

## 项目结构

```
phone-pick-assistant/
├── backend/
│   ├── main.py           # FastAPI入口
│   ├── config.py         # 配置管理
│   ├── api/routes/       # API路由
│   ├── models/           # 数据模型
│   ├── services/         # 业务服务
│   ├── utils/            # 工具函数（安全等）
│   └── data/             # 数据库与种子
├── frontend/
│   └── src/
│       ├── components/   # React组件
│       ├── services/     # API服务
│       ├── hooks/        # 自定义Hooks
│       └── types/        # TypeScript类型
├── tests/                # 测试文件
├── .gstack/              # QA报告
├── issues/               # 问题记录
└── docs/                 # 文档
```

## 测试

```bash
# 后端单元测试
pytest tests/ -v

# 前端单元测试
cd frontend && npm test
```

## 数据状态

- 手机数据: 353款
- 品牌覆盖: 17个（小米、华为、苹果、三星等）
- 图片覆盖: 93.7%

## License

MIT