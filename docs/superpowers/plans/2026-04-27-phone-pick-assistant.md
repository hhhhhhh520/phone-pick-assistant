# 手机选购助手实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个AI对话式手机选购助手，支持需求推荐、参数对比、预算筛选三种场景。

**Architecture:** FastAPI后端 + React前端，通过SSE实现流式输出。后端分层：API → Service(Intent/Retrieval/Recommend) → LLM(DeepSeek) → SQLite数据层。

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, DeepSeek API, React 18, Vite, TailwindCSS, TypeScript

---

## 文件结构

```
D:/my project/phone-pick-assistant/
├── backend/
│   ├── main.py                    # FastAPI入口
│   ├── config.py                  # 配置管理
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py            # 对话API
│   │   │   └── phones.py          # 手机数据API
│   │   └── dependencies.py        # 依赖注入
│   ├── models/
│   │   ├── domain.py              # SQLAlchemy模型
│   │   └── schemas.py             # Pydantic模型
│   ├── services/
│   │   ├── llm.py                 # DeepSeek封装
│   │   ├── intent.py              # 意图识别
│   │   ├── retrieval.py           # 手机检索
│   │   └── recommend.py           # 推荐生成
│   └── data/
│       ├── schema.sql             # 表结构
│       └── seed.py                # 种子数据
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── tests/
├── .env.example
└── requirements.txt
```

---

## Task 1: 项目初始化与后端骨架

**Files:**
- Create: `D:/my project/phone-pick-assistant/backend/main.py`
- Create: `D:/my project/phone-pick-assistant/backend/config.py`
- Create: `D:/my project/phone-pick-assistant/requirements.txt`
- Create: `D:/my project/phone-pick-assistant/.env.example`
- Create: `D:/my project/phone-pick-assistant/.gitignore`

- [ ] **Step 1: 创建项目目录结构**

```bash
cd "D:/my project"
mkdir -p phone-pick-assistant/backend/api/routes
mkdir -p phone-pick-assistant/backend/models
mkdir -p phone-pick-assistant/backend/services
mkdir -p phone-pick-assistant/backend/data
mkdir -p phone-pick-assistant/tests
```

- [ ] **Step 2: 创建 requirements.txt**

```txt
fastapi==0.110.0
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
pydantic==2.6.1
pydantic-settings==2.2.1
httpx==0.27.0
python-dotenv==1.0.1
slowapi==0.1.9
pytest==8.0.0
pytest-asyncio==0.23.4
```

- [ ] **Step 3: 创建 .env.example**

```bash
DEEPSEEK_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///./backend/data/phones.db
APP_ENV=development
LOG_LEVEL=INFO
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7
LLM_MODEL=deepseek-chat
```

- [ ] **Step 4: 创建 .gitignore**

```gitignore
__pycache__/
*.py[cod]
.venv/
.env
*.db
frontend/node_modules/
frontend/dist/
*.log
```

- [ ] **Step 5: 创建 config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    database_url: str = "sqlite:///./data/phones.db"
    app_env: str = "development"
    log_level: str = "INFO"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_model: str = "deepseek-chat"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: 创建 main.py 骨架**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.config import get_settings

settings = get_settings()

app = FastAPI(title="手机选购助手API", version="0.1.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "手机选购助手API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

- [ ] **Step 7: 安装依赖并验证**

```bash
cd "D:/my project/phone-pick-assistant"
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

- [ ] **Step 8: 提交**

```bash
git init && git add . && git commit -m "chore: 项目初始化"
```

---

## Task 2: 数据模型与数据库初始化

**Files:**
- Create: `D:/my project/phone-pick-assistant/backend/data/schema.sql`
- Create: `D:/my project/phone-pick-assistant/backend/models/domain.py`
- Create: `D:/my project/phone-pick-assistant/backend/models/schemas.py`
- Create: `D:/my project/phone-pick-assistant/backend/data/seed.py`

- [ ] **Step 1: 创建 schema.sql**

```sql
CREATE TABLE IF NOT EXISTS phones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    price INTEGER NOT NULL,
    release_date TEXT,
    screen_size REAL,
    screen_type TEXT,
    screen_refresh INTEGER,
    processor TEXT,
    ram INTEGER,
    storage INTEGER,
    camera_main INTEGER,
    camera_ultra INTEGER,
    camera_telephoto INTEGER,
    camera_front INTEGER,
    battery INTEGER,
    charging_wired INTEGER,
    charging_wireless INTEGER,
    weight INTEGER,
    features TEXT,
    url TEXT,
    pros TEXT,
    cons TEXT,
    suitable_for TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_phones_brand ON phones(brand);
CREATE INDEX IF NOT EXISTS idx_phones_price ON phones(price);
CREATE INDEX IF NOT EXISTS idx_phones_processor ON phones(processor);
```

- [ ] **Step 2: 创建 domain.py (SQLAlchemy模型)**

```python
from sqlalchemy import Column, Integer, String, Text, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import get_settings
import json

Base = declarative_base()

class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    release_date = Column(String(20))
    screen_size = Column(Float)
    screen_type = Column(String(20))
    screen_refresh = Column(Integer)
    processor = Column(String(50))
    ram = Column(Integer)
    storage = Column(Integer)
    camera_main = Column(Integer)
    camera_ultra = Column(Integer)
    camera_telephoto = Column(Integer)
    camera_front = Column(Integer)
    battery = Column(Integer)
    charging_wired = Column(Integer)
    charging_wireless = Column(Integer)
    weight = Column(Integer)
    features = Column(Text)
    url = Column(String(500))
    pros = Column(Text)
    cons = Column(Text)
    suitable_for = Column(Text)
    created_at = Column(String(30))
    updated_at = Column(String(30))

    def to_dict(self):
        return {
            "id": self.id,
            "brand": self.brand,
            "model": self.model,
            "price": self.price,
            "release_date": self.release_date,
            "screen": {"size": self.screen_size, "type": self.screen_type, "refresh": self.screen_refresh},
            "processor": self.processor,
            "ram": self.ram,
            "storage": self.storage,
            "camera": {"main": self.camera_main, "ultra": self.camera_ultra, "telephoto": self.camera_telephoto, "front": self.camera_front},
            "battery": self.battery,
            "charging": {"wired": self.charging_wired, "wireless": self.charging_wireless},
            "weight": self.weight,
            "features": json.loads(self.features) if self.features else [],
            "url": self.url,
            "pros": json.loads(self.pros) if self.pros else [],
            "cons": json.loads(self.cons) if self.cons else [],
            "suitable_for": json.loads(self.suitable_for) if self.suitable_for else []
        }

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    import sqlite3
    import os
    db_path = settings.database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.close()
```

- [ ] **Step 3: 创建 schemas.py (Pydantic模型)**

```python
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class IntentType(str, Enum):
    RECOMMEND = "recommend"
    COMPARE = "compare"
    FILTER = "filter"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class PhoneBrief(BaseModel):
    id: int
    brand: str
    model: str
    price: int

class PhoneListResponse(BaseModel):
    phones: List[PhoneBrief]
    total: int

class IntentResult(BaseModel):
    intent: IntentType
    budget_min: Optional[int] = 0
    budget_max: Optional[int] = 100000
    brands: Optional[List[str]] = []
    features: Optional[List[str]] = []
    phones_mentioned: Optional[List[str]] = []
```

- [ ] **Step 4: 创建 seed.py (种子数据)**

包含20款热门手机数据，运行后初始化数据库。

- [ ] **Step 5: 运行种子脚本验证**

```bash
cd "D:/my project/phone-pick-assistant"
python -m backend.data.seed
```

- [ ] **Step 6: 提交**

```bash
git add . && git commit -m "feat: 数据模型与种子数据"
```

---

## Task 3: LLM服务封装

**Files:**
- Create: `D:/my project/phone-pick-assistant/backend/services/llm.py`

- [ ] **Step 1: 创建 llm.py**

```python
import httpx
from backend.config import get_settings
from typing import AsyncGenerator, List, Dict

settings = get_settings()

class LLMService:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    async def chat_stream(self, messages: List[Dict], system_prompt: str = None) -> AsyncGenerator[str, None]:
        """流式对话"""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": True
                },
                timeout=60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        if data.get("choices") and data["choices"][0].get("delta", {}).get("content"):
                            yield data["choices"][0]["delta"]["content"]

    async def chat(self, messages: List[Dict], system_prompt: str = None) -> str:
        """非流式对话"""
        result = ""
        async for chunk in self.chat_stream(messages, system_prompt):
            result += chunk
        return result
```

- [ ] **Step 2: 提交**

```bash
git add . && git commit -m "feat: LLM服务封装"
```

---

## Task 4: 意图识别与检索服务

**Files:**
- Create: `D:/my project/phone-pick-assistant/backend/services/intent.py`
- Create: `D:/my project/phone-pick-assistant/backend/services/retrieval.py`

- [ ] **Step 1: 创建 intent.py**

```python
from backend.services.llm import LLMService
from backend.models.schemas import IntentResult, IntentType
import json

INTENT_PROMPT = """你是一个手机选购助手。分析用户意图并提取关键信息。

用户输入: "{user_message}"

返回JSON格式(不要有其他内容):
{{
  "intent": "recommend或compare或filter",
  "budget_min": 0,
  "budget_max": 10000,
  "brands": ["品牌列表"],
  "features": ["功能需求列表"],
  "phones_mentioned": ["提到的手机型号"]
}}

intent说明:
- recommend: 用户想要推荐手机
- compare: 用户想对比两款手机
- filter: 用户想按条件筛选
"""

class IntentService:
    def __init__(self):
        self.llm = LLMService()

    async def recognize(self, user_message: str) -> IntentResult:
        """识别用户意图"""
        prompt = INTENT_PROMPT.format(user_message=user_message)
        response = await self.llm.chat([{"role": "user", "content": prompt}])

        try:
            data = json.loads(response)
            return IntentResult(
                intent=IntentType(data.get("intent", "recommend")),
                budget_min=data.get("budget_min", 0),
                budget_max=data.get("budget_max", 100000),
                brands=data.get("brands", []),
                features=data.get("features", []),
                phones_mentioned=data.get("phones_mentioned", [])
            )
        except:
            return IntentResult(intent=IntentType.RECOMMEND)
```

- [ ] **Step 2: 创建 retrieval.py**

```python
from sqlalchemy.orm import Session
from backend.models.domain import Phone
from typing import List

class RetrievalService:
    def __init__(self, db: Session):
        self.db = db

    def get_phones_by_budget(self, min_price: int, max_price: int, limit: int = 10) -> List[Phone]:
        """按预算筛选"""
        return self.db.query(Phone).filter(
            Phone.price >= min_price,
            Phone.price <= max_price
        ).order_by(Phone.price).limit(limit).all()

    def get_phones_by_brand(self, brands: List[str], limit: int = 10) -> List[Phone]:
        """按品牌筛选"""
        return self.db.query(Phone).filter(
            Phone.brand.in_(brands)
        ).limit(limit).all()

    def get_phones_by_model(self, models: List[str]) -> List[Phone]:
        """按型号查找"""
        phones = []
        for model in models:
            phone = self.db.query(Phone).filter(
                Phone.model.contains(model)
            ).first()
            if phone:
                phones.append(phone)
        return phones

    def search(self, intent_result, limit: int = 10) -> List[Phone]:
        """综合搜索"""
        query = self.db.query(Phone)

        # 预算筛选
        if intent_result.budget_min > 0 or intent_result.budget_max < 100000:
            query = query.filter(
                Phone.price >= intent_result.budget_min,
                Phone.price <= intent_result.budget_max
            )

        # 品牌筛选
        if intent_result.brands:
            query = query.filter(Phone.brand.in_(intent_result.brands))

        return query.limit(limit).all()

    def get_all_phones(self, limit: int = 20) -> List[Phone]:
        """获取所有手机"""
        return self.db.query(Phone).limit(limit).all()
```

- [ ] **Step 3: 提交**

```bash
git add . && git commit -m "feat: 意图识别与检索服务"
```

---

## Task 5: 推荐服务与API路由

**Files:**
- Create: `D:/my project/phone-pick-assistant/backend/services/recommend.py`
- Create: `D:/my project/phone-pick-assistant/backend/api/routes/chat.py`
- Create: `D:/my project/phone-pick-assistant/backend/api/routes/phones.py`
- Create: `D:/my project/phone-pick-assistant/backend/api/dependencies.py`

- [ ] **Step 1: 创建 recommend.py**

```python
from backend.services.llm import LLMService
from backend.models.domain import Phone
from backend.models.schemas import IntentType
from typing import List, AsyncGenerator
import json

RECOMMEND_PROMPT = """你是一个专业的手机选购顾问。

用户需求: {user_need}
候选手机: {phones}

请根据用户需求推荐最合适的2-3款手机，说明推荐理由。
用简洁自然的语言回答，不要过于正式。
"""

COMPARE_PROMPT = """你是一个手机参数对比专家。

用户想对比: {phones}

请从以下维度对比:
1. 性能(处理器、内存)
2. 拍照(摄像头配置)
3. 续航(电池、充电)
4. 价格

用简洁语言总结差异，给出选择建议。
"""

class RecommendService:
    def __init__(self):
        self.llm = LLMService()

    async def recommend(self, user_need: str, phones: List[Phone]) -> AsyncGenerator[str, None]:
        """推荐手机"""
        phones_info = "\n".join([
            f"- {p.brand} {p.model}: {p.price}元, {p.processor}, {p.ram}GB内存, {p.camera_main}万像素主摄"
            for p in phones[:5]
        ])
        prompt = RECOMMEND_PROMPT.format(user_need=user_need, phones=phones_info)
        async for chunk in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            yield chunk

    async def compare(self, phones: List[Phone]) -> AsyncGenerator[str, None]:
        """对比手机"""
        phones_info = "\n".join([
            f"- {p.brand} {p.model}: {p.price}元, {p.processor}, {p.ram}GB内存, {p.camera_main}万像素, {p.battery}mAh电池"
            for p in phones
        ])
        prompt = COMPARE_PROMPT.format(phones=phones_info)
        async for chunk in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            yield chunk
```

- [ ] **Step 2: 创建 dependencies.py**

```python
from sqlalchemy.orm import Session
from backend.models.domain import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: 创建 chat.py (对话API)**

SSE流式输出，处理三种意图。

- [ ] **Step 4: 创建 phones.py (手机API)**

GET /api/phones 列表接口，GET /api/phones/{id} 详情接口。

- [ ] **Step 5: 更新 main.py 注册路由**

- [ ] **Step 6: 提交**

```bash
git add . && git commit -m "feat: 推荐服务与API路由"
```

---

## Task 6: 前端React项目初始化

**Files:**
- Create: `D:/my project/phone-pick-assistant/frontend/package.json`
- Create: `D:/my project/phone-pick-assistant/frontend/vite.config.ts`
- Create: `D:/my project/phone-pick-assistant/frontend/tailwind.config.js`
- Create: `D:/my project/phone-pick-assistant/frontend/src/main.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/App.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/index.css`

- [ ] **Step 1: 初始化Vite项目**

```bash
cd "D:/my project/phone-pick-assistant"
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 2: 配置 TailwindCSS**

- [ ] **Step 3: 创建基础组件结构**

- [ ] **Step 4: 提交**

```bash
git add . && git commit -m "feat: 前端项目初始化"
```

---

## Task 7: 前端聊天组件

**Files:**
- Create: `D:/my project/phone-pick-assistant/frontend/src/components/ChatWindow.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/components/MessageList.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/components/MessageItem.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/components/PhoneCard.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/components/InputBar.tsx`
- Create: `D:/my project/phone-pick-assistant/frontend/src/services/api.ts`
- Create: `D:/my project/phone-pick-assistant/frontend/src/types/index.ts`

- [ ] **Step 1: 创建类型定义**

- [ ] **Step 2: 创建API服务(SSE)**

- [ ] **Step 3: 创建各组件**

- [ ] **Step 4: 组装ChatWindow**

- [ ] **Step 5: 提交**

```bash
git add . && git commit -m "feat: 前端聊天组件"
```

---

## Task 8: 集成测试与文档

**Files:**
- Create: `D:/my project/phone-pick-assistant/tests/test_api.py`
- Create: `D:/my project/phone-pick-assistant/README.md`
- Create: `D:/my project/phone-pick-assistant/PROGRESS.md`

- [ ] **Step 1: 编写API测试**

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/ -v
```

- [ ] **Step 3: 编写README**

- [ ] **Step 4: 创建PROGRESS.md**

- [ ] **Step 5: 最终提交**

```bash
git add . && git commit -m "docs: 测试与文档"
```

---

## Task 9: 启动验证

- [ ] **Step 1: 启动后端**

```bash
cd "D:/my project/phone-pick-assistant"
.venv/Scripts/activate
uvicorn backend.main:app --reload --port 8000
```

- [ ] **Step 2: 启动前端**

```bash
cd frontend
npm run dev
```

- [ ] **Step 3: 测试对话功能**

打开 http://localhost:5173 测试：
- "推荐一款拍照好的手机"
- "iPhone 15和小米14哪个好"
- "3000元左右推荐几款"

---

## 验收标准

- [ ] 后端API正常运行
- [ ] 前端页面正常显示
- [ ] 对话功能正常工作
- [ ] SSE流式输出正常
- [ ] 手机卡片正常展示
- [ ] 三种意图识别正常
