# 消息列表末尾持续存在空气泡
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

多轮测试中观察到，对话消息列表 `[role="log"]` 末尾持续存在一个空的子元素（innerText 为空），使消息计数比实际多 1。出现在推荐完成、历史恢复、追问等多种场景。

## 出现原因

推测是 SSE `done` 事件后前端渲染逻辑留下的占位 div，或流式 content 拼接的边界残留。需看 ChatWindow/MessageList 的渲染逻辑确认。

## 影响

- 无功能影响，纯显示瑕疵
- 可能影响辅助技术对消息列表的读取

## 解决方案

定位渲染末尾空气泡的代码并清理（需读 ChatWindow.tsx / MessageList.tsx 确认）。

## 相关文件

- `frontend/src/components/ChatWindow.tsx`
- `frontend/src/components/MessageList.tsx`

## 参考资料

- 实测：2026-07-02 多场景观察到末尾空 div（count 比实际消息多 1）
