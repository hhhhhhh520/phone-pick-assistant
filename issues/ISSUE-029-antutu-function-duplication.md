# ISSUE-029 get_antutu_score 与 get_canonical_processor 代码重复

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）

## 问题描述

`backend/models/domain.py` 中两个函数共享 7 个匹配策略中的 6 个，代码重复度约 90%：

| 函数 | 行号 | 用途 | 返回值 |
|------|------|------|--------|
| `get_antutu_score` | 250-317 | 获取处理器跑分 | `scores[key]` (int) |
| `get_canonical_processor` | 320-374 | 获取处理器规范名称 | `key` (str) |

两个函数的匹配策略完全相同：
1. 原始字符串直接匹配
2. 规范化后直接匹配
3. 去空格后完全相等匹配
4. 规范化+去空格后完全相等匹配
5. 模糊包含匹配（双向子串）
6. 规范化后再模糊包含匹配
7. 去空格后模糊包含匹配

唯一区别：匹配成功后 `get_antutu_score` 返回 `scores[key]`，`get_canonical_processor` 返回 `key` 本身。

## 出现原因

先实现了 `get_antutu_score`（需要跑分），后来需要 `get_canonical_processor`（需要规范名称用于数据库标准化），直接复制 `get_antutu_score` 的代码并修改返回值。没有意识到可以抽取公共逻辑。

相关提交: `41998c3 feat(data): 添加安兔兔处理器跑分数据`

## 解决方案

抽取公共匹配方法 `_find_matching_key`，两个函数调用它：

```python
def _find_matching_key(scores: dict, processor: str) -> str | None:
    """
    在跑分字典中查找处理器的匹配键。

    匹配策略（按优先级）：
    1. 原始字符串直接匹配
    2. 规范化后直接匹配
    3. 去空格后完全相等匹配
    4. 规范化+去空格后完全相等匹配
    5. 模糊包含匹配（双向子串）
    6. 规范化后再模糊包含匹配
    7. 去空格后模糊包含匹配

    Returns:
        匹配到的键，未匹配返回 None
    """
    if not processor or not processor.strip():
        return None

    # 策略1: 原始字符串直接匹配
    if processor in scores:
        return processor

    # 策略2: 规范化后直接匹配
    normalized = _normalize_processor(processor)
    if normalized and normalized in scores:
        return normalized

    # 策略3: 去空格后完全相等匹配
    processor_no_space = processor.replace(" ", "")
    for key in scores:
        if key.replace(" ", "") == processor_no_space:
            return key

    # 策略4: 规范化+去空格后完全相等匹配
    if normalized:
        norm_no_space = normalized.replace(" ", "")
        for key in scores:
            if key.replace(" ", "") == norm_no_space:
                return key

    # 策略5: 模糊包含匹配（双向子串）
    processor_lower = processor.lower()
    for key in scores:
        if processor_lower in key.lower() or key.lower() in processor_lower:
            return key

    # 策略6: 规范化后再模糊包含匹配
    if normalized:
        norm_lower = normalized.lower()
        for key in scores:
            if norm_lower in key.lower() or key.lower() in norm_lower:
                return key

    # 策略7: 去空格后模糊包含匹配
    for key in scores:
        kns = key.replace(" ", "").lower()
        pns = (normalized.replace(" ", "") if normalized else processor_no_space).lower()
        if pns in kns or kns in pns:
            return key

    return None


def get_antutu_score(processor: str) -> int:
    """获取处理器的安兔兔跑分，未知处理器返回0。"""
    scores, _ = _get_antutu_data()
    key = _find_matching_key(scores, processor)
    return scores[key] if key else 0


def get_canonical_processor(processor: str) -> str:
    """返回处理器的规范形式，无法匹配则返回原始值。"""
    if not processor:
        return processor or ""
    scores, _ = _get_antutu_data()
    key = _find_matching_key(scores, processor)
    if key:
        return key
    normalized = _normalize_processor(processor)
    return normalized if normalized else processor
```

## 影响面

- 功能影响：无。两个函数的外部接口和返回值完全不变
- 测试影响：`test_camera_scoring.py` 和 `test_data_completeness.py` 覆盖了这两个函数
- 风险等级：零（纯重构，接口不变）

## 验证方法

1. 运行现有测试：`pytest tests/test_camera_scoring.py tests/test_data_completeness.py -v`
2. 确认 `get_antutu_score` 返回值不变
3. 确认 `get_canonical_processor` 返回值不变
4. 确认 `_find_matching_key` 返回 None 时两个函数的 fallback 行为正确

## 相关文件

- `backend/models/domain.py:250-374` — 重构目标

## 参考资料

- 相关提交: `41998c3 feat(data): 添加安兔兔处理器跑分数据`
