# ISSUE-030 to_dict() 中 4 个相同的 JSON 解析块

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）

## 问题描述

`backend/models/domain.py` 的 `Phone.to_dict()` 方法（46-106 行）对 `features`、`suitable_for`、`pros`、`cons` 四个字段使用完全相同的 JSON 解析 + 异常处理模式，重复 4 次：

```python
# 这段代码重复了 4 次，只是变量名不同
xxx_list = []
if self.xxx:
    try:
        xxx_list = json.loads(self.xxx)
    except (json.JSONDecodeError, TypeError):
        xxx_list = []
```

## 出现原因

初始实现时逐个字段添加 JSON 解析，没有抽取公共方法。这是典型的"复制粘贴编程"。

## 解决方案

抽取 `_parse_json_field` 静态方法：

```python
@staticmethod
def _parse_json_field(value, default=None):
    """解析 JSON 字段，处理 None 和无效 JSON。"""
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
```

然后 `to_dict()` 简化为：

```python
def to_dict(self):
    return {
        ...
        "features": self._parse_json_field(self.features),
        "suitable_for": self._parse_json_field(self.suitable_for),
        "pros": self._parse_json_field(self.pros),
        "cons": self._parse_json_field(self.cons),
    }
```

## 影响面

- 功能影响：无。`to_dict()` 返回值完全不变
- 测试影响：任何调用 `phone.to_dict()` 的测试都会验证
- 风险等级：零（纯重构，接口不变）

## 验证方法

1. 运行现有测试：`pytest tests/ -v`
2. 确认 `to_dict()` 返回值的 JSON 序列化结果不变

## 相关文件

- `backend/models/domain.py:46-106` — 重构目标
