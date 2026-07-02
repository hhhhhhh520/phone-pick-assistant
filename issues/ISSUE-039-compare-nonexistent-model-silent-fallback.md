# 对比模式：不存在的型号静默回退，用户无感知
> 创建时间: 2026-07-02 | 状态: 🟢已解决

## 问题描述

用户输入"对比一下 钢铁侠手机 和 蜘蛛侠手机"（数据库中不存在的型号），系统没有提示"未找到该型号"，而是**静默回退**到 `get_all_phones(2)`，对比了努比亚小牛和 Redmi Note 两款入门机。用户完全不知道展示的不是自己要的机型。

## 出现原因

`backend/api/routes/chat.py:150-154` 对比分支：
```python
phones = retrieval_service.get_phones_by_model(intent_result.phones_mentioned)
if len(phones) < 2:
    phones = retrieval_service.get_all_phones(2)  # 静默回退，无任何提示
```

`get_phones_by_model` 对找不到的型号返回空列表，触发回退到全库前 2 款（按"有图片优先"排序，恰好是便宜的入门机），且 LLM 收到的是这俩无关机型，硬着头皮做对比。

## 影响

- 用户对比"钢铁侠手机 vs 蜘蛛侠手机"，得到"努比亚小牛 vs Redmi Note"的对比，**误导性强**
- 与 ISSUE-036 同类问题：回退逻辑不告知用户、丢失用户意图

## 解决方案

回退时应：
1. 若用户明确提到型号但全部未找到，发送提示事件（如"未找到 钢铁侠手机，已为您推荐其他热门机型"）让前端展示
2. 或不回退，直接让 LLM 告知"未找到该型号"
3. 至少在 SSE 中加一个 `notice`/`warning` 事件，前端展示提示

## 相关文件

- `backend/api/routes/chat.py:150-154`

## 参考资料

- 与 ISSUE-036 同属"回退失效"类问题
- 实测：2026-07-02 无头浏览器测试发现
