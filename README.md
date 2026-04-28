# 手机选购助手

AI对话式手机选购助手，支持需求推荐、参数对比、预算筛选三种场景。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite + DeepSeek API
- **前端**: React 18 + Vite + TailwindCSS + TypeScript
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
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 初始化数据库
python -m backend.data.seed

# 启动服务
uvicorn backend.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev
```

访问 http://localhost:5173

## 功能特性

- **智能推荐**: 根据用户需求推荐合适的手机
- **参数对比**: 对比两款手机的各项参数
- **预算筛选**: 按价格区间筛选手机
- **流式输出**: SSE实时显示AI回复
- **手机卡片**: 展示手机关键信息

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 对话接口(SSE) |
| `/api/phones` | GET | 手机列表 |
| `/api/phones/{id}` | GET | 手机详情 |

## 项目结构

```
phone-pick-assistant/
├── backend/
│   ├── main.py           # FastAPI入口
│   ├── config.py         # 配置管理
│   ├── api/routes/       # API路由
│   ├── models/           # 数据模型
│   ├── services/         # 业务服务
│   └── data/             # 数据库与种子
├── frontend/
│   └── src/
│       ├── components/   # React组件
│       ├── services/     # API服务
│       └── types/        # TypeScript类型
└── tests/                # 测试文件
```

## 测试

```bash
pytest tests/ -v
```

## License

MIT
