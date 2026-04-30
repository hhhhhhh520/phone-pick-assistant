# 手机选购助手正式版功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为手机选购助手添加搜索历史、手机图片、对比表格、多轮对话四个功能

**Architecture:** 前端使用 React + localStorage，后端使用 FastAPI 内存会话管理，保持现有 SSE 流式架构

**Tech Stack:** React, TypeScript, FastAPI, SQLite, DeepSeek API

---

## 文件结构

```
frontend/src/
├── hooks/
│   ├── useSearchHistory.ts  (新建) - 搜索历史Hook
│   └── useSession.ts        (新建) - 会话管理Hook
├── components/
│   ├── SearchHistory.tsx    (新建) - 搜索历史组件
│   ├── CompareTable.tsx     (新建) - 对比表格组件
│   ├── ChatWindow.tsx       (修改) - 集成历史和会话
│   ├── MessageItem.tsx      (修改) - 渲染对比表格
│   └── PhoneCard.tsx        (修改) - 添加图片展示
├── services/
│   └── api.ts               (修改) - 添加session_id
└── types/
    └── index.ts             (修改) - 添加imageUrl

backend/
├── services/
│   ├── session.py           (新建) - 会话管理服务
│   ├── llm.py               (修改) - 支持历史消息
│   └── recommend.py         (修改) - 对比逻辑
├── models/
│   ├── domain.py            (修改) - 添加image_url
│   └── schemas.py           (修改) - 添加session_id
├── api/routes/
│   └── chat.py              (修改) - 会话逻辑
└── data/
    └── seed.py              (修改) - 添加图片URL
```

---

## Task 1: 搜索历史

**Files:**
- Create: `frontend/src/hooks/useSearchHistory.ts`
- Create: `frontend/src/components/SearchHistory.tsx`
- Modify: `frontend/src/components/ChatWindow.tsx`
- Modify: `frontend/src/types/index.ts`

### Step 1: 添加类型定义

- [ ] **修改 `frontend/src/types/index.ts`**

```typescript
// 在文件末尾添加

export interface SearchHistoryItem {
  id: string;
  query: string;
  phones: Phone[];
  timestamp: number;
}
```

### Step 2: 创建搜索历史Hook

- [ ] **创建 `frontend/src/hooks/useSearchHistory.ts`**

```typescript
import { useState, useEffect, useCallback } from 'react';
import type { Phone, SearchHistoryItem } from '../types';

const STORAGE_KEY = 'phone_search_history';
const MAX_HISTORY = 20;

export function useSearchHistory() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);

  // 从localStorage加载历史
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setHistory(JSON.parse(stored));
      } catch {
        setHistory([]);
      }
    }
  }, []);

  // 保存到localStorage
  const saveHistory = useCallback((items: SearchHistoryItem[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    setHistory(items);
  }, []);

  // 添加历史记录
  const addHistory = useCallback((query: string, phones: Phone[]) => {
    const newItem: SearchHistoryItem = {
      id: Date.now().toString(),
      query,
      phones,
      timestamp: Date.now(),
    };

    setHistory((prev) => {
      const filtered = prev.filter((item) => item.query !== query);
      const updated = [newItem, ...filtered].slice(0, MAX_HISTORY);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  // 清空历史
  const clearHistory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setHistory([]);
  }, []);

  return {
    history,
    addHistory,
    clearHistory,
  };
}
```

### Step 3: 创建搜索历史组件

- [ ] **创建 `frontend/src/components/SearchHistory.tsx`**

```typescript
import type { SearchHistoryItem } from '../types';

interface SearchHistoryProps {
  history: SearchHistoryItem[];
  onSelect: (item: SearchHistoryItem) => void;
  onClear: () => void;
}

export function SearchHistory({ history, onSelect, onClear }: SearchHistoryProps) {
  if (history.length === 0) {
    return null;
  }

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">搜索历史</span>
        <button
          onClick={onClear}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          清空
        </button>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {history.slice(0, 10).map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            className="flex-shrink-0 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-700 transition-colors"
          >
            <span className="truncate max-w-[120px] inline-block">{item.query}</span>
            <span className="text-gray-400 text-xs ml-1">
              {formatTime(item.timestamp)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### Step 4: 集成到ChatWindow

- [ ] **修改 `frontend/src/components/ChatWindow.tsx`**

```typescript
import { useState } from 'react';
import type { Message, Phone, SearchHistoryItem } from '../types';
import { chatStream } from '../services/api';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { SearchHistory } from './SearchHistory';
import { useSearchHistory } from '../hooks/useSearchHistory';

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const { history, addHistory, clearHistory } = useSearchHistory();

  const handleSend = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      phones: [],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    let phones: Phone[] = [];

    try {
      for await (const event of chatStream(content)) {
        if (event.type === 'phones') {
          phones = event.data as Phone[];
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id ? { ...m, phones } : m
            )
          );
        } else if (event.type === 'content') {
          const chunk = event.data as string;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: m.content + chunk }
                : m
            )
          );
        }
      }

      // 保存搜索历史
      if (phones.length > 0) {
        addHistory(content, phones);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: `抱歉，发生了错误：${error instanceof Error ? error.message : String(error)}` }
            : m
        )
      );
    }

    setLoading(false);
  };

  // 从历史记录恢复对话
  const handleHistorySelect = (item: SearchHistoryItem) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: item.query,
      timestamp: new Date(),
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '以下是之前的推荐结果：',
      phones: item.phones,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-xl font-semibold text-gray-800">📱 手机选购助手</h1>
      </header>

      <SearchHistory
        history={history}
        onSelect={handleHistorySelect}
        onClear={clearHistory}
      />

      <MessageList messages={messages} />

      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
```

### Step 5: 验证

- [ ] **启动前端验证搜索历史功能**

```bash
cd "D:\my project\phone-pick-assistant\frontend"
npm run dev
```

验证：
1. 发起多次对话，历史记录正确显示
2. 点击历史项可恢复之前的推荐结果
3. 清空历史功能正常

### Step 6: 提交

```bash
cd "D:\my project\phone-pick-assistant"
git add frontend/src/hooks/useSearchHistory.ts frontend/src/components/SearchHistory.tsx frontend/src/components/ChatWindow.tsx frontend/src/types/index.ts
git commit -m "feat: 添加搜索历史功能

- 创建 useSearchHistory Hook，使用 localStorage 存储
- 创建 SearchHistory 组件，展示历史列表
- 集成到 ChatWindow，支持点击恢复历史对话

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 2: 手机图片

**Files:**
- Modify: `backend/models/domain.py`
- Modify: `backend/data/seed.py`
- Modify: `frontend/src/components/PhoneCard.tsx`
- Modify: `frontend/src/types/index.ts`

### Step 1: 后端添加image_url字段

- [ ] **修改 `backend/models/domain.py`**

在 `Phone` 类中添加 `image_url` 字段（在 `url` 字段后添加）：

```python
# 在第32行 url = Column(String(500)) 后添加
image_url = Column(String(500))
```

修改 `to_dict` 方法，添加 `imageUrl`：

```python
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
        "camera": {
            "main": self.camera_main,
            "ultra": self.camera_ultra,
            "telephoto": self.camera_telephoto,
            "front": self.camera_front
        },
        "battery": self.battery,
        "charging": {"wired": self.charging_wired, "wireless": self.charging_wireless},
        "weight": self.weight,
        "features": json.loads(self.features) if self.features else [],
        "url": self.url,
        "imageUrl": self.image_url,  # 新增
        "pros": json.loads(self.pros) if self.pros else [],
        "cons": json.loads(self.cons) if self.cons else [],
        "suitable_for": json.loads(self.suitable_for) if self.suitable_for else []
    }
```

### Step 2: 更新数据库schema

- [ ] **修改 `backend/data/schema.sql`**

如果存在 schema.sql，添加 image_url 列。如果不存在，需要重建数据库。

### Step 3: 更新seed.py添加图片URL

- [ ] **修改 `backend/data/seed.py`**

为每款手机添加 `image_url` 字段。以下是部分热门机型的京东图片URL：

```python
# 在 PHONES_DATA 的每个手机数据中添加 image_url 字段
# 示例（仅列出部分热门机型）：

# iPhone 15 Pro Max
{
    "brand": "Apple",
    "model": "iPhone 15 Pro Max",
    "price": 9999,
    # ... 其他字段 ...
    "image_url": "https://img14.360buyimg.com/n1/s450x450_jfs/t1/239588/15/22990/69852/654a6b5fF6b3b3b3b/1234567890abcdef.jpg",
},

# 小米14 Ultra
{
    "brand": "小米",
    "model": "小米14 Ultra",
    "price": 6499,
    # ... 其他字段 ...
    "image_url": "https://img14.360buyimg.com/n1/s450x450_jfs/t1/123456/78/12345/67890/654a6b5fF12345678/abcdef123456.jpg",
},
```

**注意**: 实际实现时需要收集真实图片URL。可以使用占位图作为临时方案：

```python
# 临时占位图方案
"image_url": f"https://via.placeholder.com/200x200?text={brand}+{model.replace(' ', '+')}"
```

在 `seed_database` 函数中添加 image_url：

```python
# 在第1429行 url=phone_data.get("url"), 后添加
image_url=phone_data.get("image_url"),
```

### Step 4: 前端类型定义

- [ ] **修改 `frontend/src/types/index.ts`**

在 `Phone` 接口中添加 `imageUrl`：

```typescript
export interface Phone {
  id: number;
  brand: string;
  model: string;
  price: number;
  release_date?: string;
  screen: {
    size: number;
    type: string;
    refresh: number;
  };
  processor: string;
  ram: number;
  storage: number;
  camera: {
    main: number;
    ultra: number;
    telephoto: number;
    front: number;
  };
  battery: number;
  charging: {
    wired: number;
    wireless: number;
  };
  weight: number;
  features: string[];
  url?: string;
  imageUrl?: string;  // 新增
  pros: string[];
  cons: string[];
  suitable_for: string[];
}
```

### Step 5: 更新PhoneCard组件

- [ ] **修改 `frontend/src/components/PhoneCard.tsx`**

```typescript
import type { Phone } from '../types';

interface PhoneCardProps {
  phone: Phone;
  onClick?: () => void;
}

export function PhoneCard({ phone, onClick }: PhoneCardProps) {
  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      {/* 手机图片 */}
      {phone.imageUrl ? (
        <div className="mb-3 flex justify-center">
          <img
            src={phone.imageUrl}
            alt={`${phone.brand} ${phone.model}`}
            className="w-24 h-24 object-contain"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'https://via.placeholder.com/96x96?text=No+Image';
            }}
          />
        </div>
      ) : null}

      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm text-gray-500">{phone.brand}</span>
          <h3 className="font-medium text-gray-900">{phone.model}</h3>
        </div>
        <span className="text-lg font-semibold text-blue-600">¥{phone.price}</span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
        <div>
          <span className="text-gray-400">处理器:</span> {phone.processor}
        </div>
        <div>
          <span className="text-gray-400">内存:</span> {phone.ram}GB
        </div>
        <div>
          <span className="text-gray-400">存储:</span> {phone.storage}GB
        </div>
        <div>
          <span className="text-gray-400">电池:</span> {phone.battery}mAh
        </div>
      </div>

      {phone.features.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {phone.features.slice(0, 3).map((feature, i) => (
            <span
              key={i}
              className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded"
            >
              {feature}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Step 6: 重建数据库

- [ ] **删除旧数据库并重新seed**

```bash
cd "D:\my project\phone-pick-assistant"
rm -f backend/data/phones.db
python -m backend.data.seed
```

### Step 7: 验证

- [ ] **启动服务验证图片显示**

```bash
# 后端
cd "D:\my project\phone-pick-assistant"
python -m uvicorn backend.main:app --reload --port 8002

# 前端（另一个终端）
cd "D:\my project\phone-pick-assistant\frontend"
npm run dev
```

验证：
1. 手机卡片正确显示图片
2. 无图片时显示占位符
3. 图片加载失败时显示错误提示

### Step 8: 提交

```bash
cd "D:\my project\phone-pick-assistant"
git add backend/models/domain.py backend/data/seed.py frontend/src/components/PhoneCard.tsx frontend/src/types/index.ts
git commit -m "feat: 添加手机图片展示功能

- 后端 Phone 模型添加 image_url 字段
- 前端 PhoneCard 组件展示手机图片
- 支持图片加载失败时显示占位符

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 3: 对比表格

**Files:**
- Create: `frontend/src/components/CompareTable.tsx`
- Modify: `frontend/src/components/MessageItem.tsx`
- Modify: `backend/services/recommend.py`
- Modify: `backend/models/schemas.py`

### Step 1: 创建对比表格组件

- [ ] **创建 `frontend/src/components/CompareTable.tsx`**

```typescript
import type { Phone } from '../types';

interface CompareTableProps {
  phones: Phone[];
}

export function CompareTable({ phones }: CompareTableProps) {
  if (phones.length < 2) {
    return null;
  }

  const [phone1, phone2] = phones;

  // 判断两个值是否不同
  const isDifferent = (a: number | string | undefined, b: number | string | undefined) => {
    if (a === undefined || b === undefined) return false;
    return a !== b;
  };

  // 格式化价格
  const formatPrice = (price: number) => `¥${price.toLocaleString()}`;

  const rows = [
    { label: '品牌', value1: phone1.brand, value2: phone2.brand },
    { label: '型号', value1: phone1.model, value2: phone2.model },
    { label: '价格', value1: formatPrice(phone1.price), value2: formatPrice(phone2.price), highlight: isDifferent(phone1.price, phone2.price) },
    { label: '处理器', value1: phone1.processor, value2: phone2.processor, highlight: isDifferent(phone1.processor, phone2.processor) },
    { label: '内存', value1: `${phone1.ram}GB`, value2: `${phone2.ram}GB`, highlight: isDifferent(phone1.ram, phone2.ram) },
    { label: '存储', value1: `${phone1.storage}GB`, value2: `${phone2.storage}GB`, highlight: isDifferent(phone1.storage, phone2.storage) },
    { label: '屏幕', value1: `${phone1.screen.size}" ${phone1.screen.refresh}Hz`, value2: `${phone2.screen.size}" ${phone2.screen.refresh}Hz` },
    { label: '电池', value1: `${phone1.battery}mAh`, value2: `${phone2.battery}mAh`, highlight: isDifferent(phone1.battery, phone2.battery) },
    { label: '主摄', value1: `${phone1.camera.main}MP`, value2: `${phone2.camera.main}MP`, highlight: isDifferent(phone1.camera.main, phone2.camera.main) },
    { label: '快充', value1: `${phone1.charging.wired}W`, value2: `${phone2.charging.wired}W`, highlight: isDifferent(phone1.charging.wired, phone2.charging.wired) },
    { label: '重量', value1: `${phone1.weight}g`, value2: `${phone2.weight}g`, highlight: isDifferent(phone1.weight, phone2.weight) },
  ];

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50">
            <th className="border border-gray-200 px-3 py-2 text-left text-gray-600 w-24">参数</th>
            <th className="border border-gray-200 px-3 py-2 text-center text-gray-900 font-medium">
              {phone1.brand} {phone1.model}
            </th>
            <th className="border border-gray-200 px-3 py-2 text-center text-gray-900 font-medium">
              {phone2.brand} {phone2.model}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={row.label}
              className={row.highlight ? 'bg-yellow-50' : index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
            >
              <td className="border border-gray-200 px-3 py-2 text-gray-500">{row.label}</td>
              <td className={`border border-gray-200 px-3 py-2 text-center ${row.highlight ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                {row.value1 || '-'}
              </td>
              <td className={`border border-gray-200 px-3 py-2 text-center ${row.highlight ? 'font-medium text-gray-900' : 'text-gray-700'}`}>
                {row.value2 || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Step 2: 修改MessageItem渲染对比表格

- [ ] **修改 `frontend/src/components/MessageItem.tsx`**

```typescript
import type { Message } from '../types';
import { PhoneCard } from './PhoneCard';
import { CompareTable } from './CompareTable';

interface MessageItemProps {
  message: Message;
  isCompare?: boolean;  // 新增：是否为对比消息
}

export function MessageItem({ message, isCompare }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] ${
          isUser
            ? 'bg-blue-500 text-white rounded-2xl rounded-br-md'
            : 'bg-white border border-gray-200 rounded-2xl rounded-bl-md'
        } px-4 py-3`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.phones && message.phones.length > 0 && (
          isCompare ? (
            <CompareTable phones={message.phones} />
          ) : (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {message.phones.map((phone) => (
                <PhoneCard key={phone.id} phone={phone} />
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
```

### Step 3: 更新Message类型

- [ ] **修改 `frontend/src/types/index.ts`**

在 `Message` 接口中添加 `isCompare` 字段：

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  phones?: Phone[];
  isCompare?: boolean;  // 新增
  timestamp: Date;
}
```

### Step 4: 修改ChatWindow处理对比意图

- [ ] **修改 `frontend/src/components/ChatWindow.tsx`**

在 `handleSend` 函数中处理对比意图：

```typescript
// 在 for await 循环中添加 intent 处理
let isCompare = false;

for await (const event of chatStream(content)) {
  if (event.type === 'intent') {
    isCompare = (event.data as string) === 'compare';
  } else if (event.type === 'phones') {
    phones = event.data as Phone[];
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantMessage.id ? { ...m, phones, isCompare } : m
      )
    );
  } else if (event.type === 'content') {
    // ... 原有逻辑
  }
}
```

### Step 5: 验证

- [ ] **启动服务验证对比表格**

```bash
# 后端
python -m uvicorn backend.main:app --reload --port 8002

# 前端
npm run dev
```

验证：
1. 输入"对比小米14和华为P60"
2. 显示纵向对比表格
3. 差异项正确高亮

### Step 6: 提交

```bash
cd "D:\my project\phone-pick-assistant"
git add frontend/src/components/CompareTable.tsx frontend/src/components/MessageItem.tsx frontend/src/types/index.ts frontend/src/components/ChatWindow.tsx
git commit -m "feat: 添加手机对比表格功能

- 创建 CompareTable 组件，纵向对比参数
- 差异项高亮显示
- 集成到 MessageItem 根据意图渲染

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 4: 多轮对话

**Files:**
- Create: `backend/services/session.py`
- Modify: `backend/api/routes/chat.py`
- Modify: `backend/services/llm.py`
- Modify: `backend/models/schemas.py`
- Modify: `frontend/src/services/api.ts`
- Create: `frontend/src/hooks/useSession.ts`
- Modify: `frontend/src/components/ChatWindow.tsx`

### Step 1: 创建会话管理服务

- [ ] **创建 `backend/services/session.py`**

```python
"""
会话管理服务 - 内存存储
"""
import uuid
from typing import Dict, List, Optional
from datetime import datetime

# 会话存储：session_id -> messages
sessions: Dict[str, List[Dict]] = {}

# 每个会话最大保留消息数
MAX_MESSAGES = 20  # 10轮对话


class SessionService:
    def __init__(self):
        pass

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
        return session_id

    def get_session(self, session_id: str) -> Optional[List[Dict]]:
        """获取会话历史"""
        return sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息到会话"""
        if session_id not in sessions:
            sessions[session_id] = []

        sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 保留最近的消息
        if len(sessions[session_id]) > MAX_MESSAGES:
            sessions[session_id] = sessions[session_id][-MAX_MESSAGES:]

    def get_messages(self, session_id: str) -> List[Dict]:
        """获取会话消息列表（用于LLM上下文）"""
        messages = sessions.get(session_id, [])
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return session_id in sessions
```

### Step 2: 修改ChatRequest添加session_id

- [ ] **修改 `backend/models/schemas.py`**

ChatRequest 已有 session_id 字段，无需修改。

### Step 3: 修改chat路由处理会话

- [ ] **修改 `backend/api/routes/chat.py`**

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.api.dependencies import get_db
from backend.models.schemas import ChatRequest, IntentType
from backend.services.intent import IntentService
from backend.services.retrieval import RetrievalService
from backend.services.recommend import RecommendService
from backend.services.session import SessionService
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 会话服务实例
session_service = SessionService()


@router.post("")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """对话接口 - SSE流式输出，支持多轮对话"""
    intent_service = IntentService()
    retrieval_service = RetrievalService(db)
    recommend_service = RecommendService()

    # 会话管理
    session_id = request.session_id
    if not session_id or not session_service.session_exists(session_id):
        session_id = session_service.create_session()

    # 添加用户消息到会话
    session_service.add_message(session_id, "user", request.message)

    # 获取会话历史
    history = session_service.get_messages(session_id)

    # 识别意图
    intent_result = await intent_service.recognize(request.message)

    async def generate():
        # 发送session_id
        yield f"data: {json.dumps({'type': 'session', 'data': session_id}, ensure_ascii=False)}\n\n"

        # 发送意图信息
        yield f"data: {json.dumps({'type': 'intent', 'data': intent_result.intent.value}, ensure_ascii=False)}\n\n"

        if intent_result.intent == IntentType.COMPARE:
            # 对比模式
            phones = retrieval_service.get_phones_by_model(intent_result.phones_mentioned)
            if len(phones) < 2:
                phones = retrieval_service.get_all_phones(2)

            phones_data = [p.to_dict() for p in phones]
            yield f"data: {json.dumps({'type': 'phones', 'data': phones_data}, ensure_ascii=False)}\n\n"

            # 流式输出对比结果（传入历史）
            assistant_content = ""
            async for chunk in recommend_service.compare(phones, history):
                assistant_content += chunk
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

            # 保存助手回复
            session_service.add_message(session_id, "assistant", assistant_content)

        else:
            # 推荐/筛选模式
            phones = retrieval_service.search(intent_result, limit=5)
            if not phones:
                phones = retrieval_service.get_all_phones(5)

            phones_data = [p.to_dict() for p in phones]
            yield f"data: {json.dumps({'type': 'phones', 'data': phones_data}, ensure_ascii=False)}\n\n"

            # 流式输出推荐结果（传入历史）
            assistant_content = ""
            async for chunk in recommend_service.recommend(request.message, phones, history):
                assistant_content += chunk
                yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"

            # 保存助手回复
            session_service.add_message(session_id, "assistant", assistant_content)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Step 4: 修改recommend服务支持历史

- [ ] **修改 `backend/services/recommend.py`**

```python
from backend.services.llm import LLMService
from backend.models.domain import Phone
from backend.models.schemas import IntentType
from typing import List, AsyncGenerator, Dict

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

# 多轮对话系统提示
SYSTEM_PROMPT = """你是一个专业的手机选购顾问。你正在与用户进行多轮对话，帮助他们选择合适的手机。
请根据对话历史理解用户的真实需求，给出专业、友好的建议。
回答要简洁自然，不要过于正式。"""


class RecommendService:
    def __init__(self):
        self.llm = LLMService()

    async def recommend(self, user_need: str, phones: List[Phone], history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """推荐手机"""
        phones_info = "\n".join([
            f"- {p.brand} {p.model}: {p.price}元, {p.processor}, {p.ram}GB内存, {p.camera_main}万像素主摄"
            for p in phones[:5]
        ])

        # 构建消息
        messages = []
        if history:
            messages.extend(history)

        prompt = RECOMMEND_PROMPT.format(user_need=user_need, phones=phones_info)
        messages.append({"role": "user", "content": prompt})

        async for chunk in self.llm.chat_stream(messages, SYSTEM_PROMPT):
            yield chunk

    async def compare(self, phones: List[Phone], history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """对比手机"""
        phones_info = "\n".join([
            f"- {p.brand} {p.model}: {p.price}元, {p.processor}, {p.ram}GB内存, {p.camera_main}万像素, {p.battery}mAh电池"
            for p in phones
        ])

        # 构建消息
        messages = []
        if history:
            messages.extend(history)

        prompt = COMPARE_PROMPT.format(phones=phones_info)
        messages.append({"role": "user", "content": prompt})

        async for chunk in self.llm.chat_stream(messages, SYSTEM_PROMPT):
            yield chunk
```

### Step 5: 前端创建会话Hook

- [ ] **创建 `frontend/src/hooks/useSession.ts`**

```typescript
import { useState, useEffect, useCallback } from 'react';

const SESSION_KEY = 'phone_picker_session';

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  // 从localStorage加载session_id
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      setSessionId(stored);
    }
  }, []);

  // 保存session_id
  const saveSession = useCallback((id: string) => {
    localStorage.setItem(SESSION_KEY, id);
    setSessionId(id);
  }, []);

  // 清除session
  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    setSessionId(null);
  }, []);

  return {
    sessionId,
    saveSession,
    clearSession,
  };
}
```

### Step 6: 修改API服务携带session_id

- [ ] **修改 `frontend/src/services/api.ts`**

```typescript
import type { Phone } from '../types';

const API_BASE = 'http://localhost:8002';

export async function* chatStream(
  message: string,
  sessionId?: string | null
): AsyncGenerator<{ type: string; data: unknown }> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId || undefined,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No reader available');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch {
          // Ignore parse errors
        }
      }
    }
  }
}

export async function getPhones(params?: {
  brand?: string;
  min_price?: number;
  max_price?: number;
  limit?: number;
}): Promise<{ phones: Phone[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.brand) searchParams.set('brand', params.brand);
  if (params?.min_price) searchParams.set('min_price', String(params.min_price));
  if (params?.max_price) searchParams.set('max_price', String(params.max_price));
  if (params?.limit) searchParams.set('limit', String(params.limit));

  const response = await fetch(`${API_BASE}/api/phones?${searchParams}`);
  return response.json();
}

export async function getPhone(id: number): Promise<Phone> {
  const response = await fetch(`${API_BASE}/api/phones/${id}`);
  return response.json();
}
```

### Step 7: 集成到ChatWindow

- [ ] **修改 `frontend/src/components/ChatWindow.tsx`**

添加会话管理：

```typescript
import { useState } from 'react';
import type { Message, Phone, SearchHistoryItem } from '../types';
import { chatStream } from '../services/api';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { SearchHistory } from './SearchHistory';
import { useSearchHistory } from '../hooks/useSearchHistory';
import { useSession } from '../hooks/useSession';

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const { history, addHistory, clearHistory } = useSearchHistory();
  const { sessionId, saveSession } = useSession();

  const handleSend = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      phones: [],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    let phones: Phone[] = [];
    let isCompare = false;
    let newSessionId = sessionId;

    try {
      for await (const event of chatStream(content, sessionId)) {
        if (event.type === 'session') {
          newSessionId = event.data as string;
          saveSession(newSessionId);
        } else if (event.type === 'intent') {
          isCompare = (event.data as string) === 'compare';
        } else if (event.type === 'phones') {
          phones = event.data as Phone[];
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id ? { ...m, phones, isCompare } : m
            )
          );
        } else if (event.type === 'content') {
          const chunk = event.data as string;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: m.content + chunk }
                : m
            )
          );
        }
      }

      // 保存搜索历史
      if (phones.length > 0 && !isCompare) {
        addHistory(content, phones);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? { ...m, content: `抱歉，发生了错误：${error instanceof Error ? error.message : String(error)}` }
            : m
        )
      );
    }

    setLoading(false);
  };

  // 从历史记录恢复对话
  const handleHistorySelect = (item: SearchHistoryItem) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: item.query,
      timestamp: new Date(),
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '以下是之前的推荐结果：',
      phones: item.phones,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-xl font-semibold text-gray-800">📱 手机选购助手</h1>
      </header>

      <SearchHistory
        history={history}
        onSelect={handleHistorySelect}
        onClear={clearHistory}
      />

      <MessageList messages={messages} />

      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
```

### Step 8: 验证多轮对话

- [ ] **启动服务验证多轮对话**

```bash
# 后端
python -m uvicorn backend.main:app --reload --port 8002

# 前端
npm run dev
```

验证场景：
1. 用户问"推荐3000元的手机"
2. 用户追问"有没有便宜点的"
3. 系统理解上下文，推荐2000-2500元手机

### Step 9: 提交

```bash
cd "D:\my project\phone-pick-assistant"
git add backend/services/session.py backend/api/routes/chat.py backend/services/recommend.py frontend/src/hooks/useSession.ts frontend/src/services/api.ts frontend/src/components/ChatWindow.tsx
git commit -m "feat: 添加多轮对话功能

- 创建 SessionService 内存会话管理
- 后端支持 session_id，保留最近10轮对话
- LLM 调用传入历史消息作为上下文
- 前端 localStorage 存储 session_id

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## 最终验证

- [ ] **运行完整测试**

```bash
# 启动后端
cd "D:\my project\phone-pick-assistant"
python -m uvicorn backend.main:app --reload --port 8002

# 启动前端（另一个终端）
cd "D:\my project\phone-pick-assistant\frontend"
npm run dev
```

验证清单：
1. [ ] 搜索历史：发起多次对话，历史正确显示，点击可恢复
2. [ ] 手机图片：手机卡片显示图片，加载失败显示占位符
3. [ ] 对比表格：对比两款手机，表格正确显示，差异高亮
4. [ ] 多轮对话：追问时系统理解上下文

---

## 更新PROGRESS.md

完成后更新项目进度文档：

```markdown
### ✅ 已完成
| 阶段 | 内容 | 文件 | 完成日期 |
|------|------|------|----------|
| Task 10 | 搜索历史 | useSearchHistory.ts, SearchHistory.tsx | 2026-04-28 |
| Task 11 | 手机图片 | domain.py, PhoneCard.tsx | 2026-04-28 |
| Task 12 | 对比表格 | CompareTable.tsx | 2026-04-28 |
| Task 13 | 多轮对话 | session.py, useSession.ts | 2026-04-28 |
```
