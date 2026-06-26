# ISSUE-031 函数内 import 标准库（4 处）

> 创建时间: 2026-06-25
> 状态: 🟢 已解决（2026-06-25）

## 问题描述

4 处在函数体内部导入标准库模块，隐藏了文件的依赖关系，不符合 PEP 8 规范。

| 文件 | 行号 | 导入 | 调用频率 |
|------|------|------|----------|
| `backend/models/domain.py` | 235 | `import re` | 每次调用 `_normalize_processor` |
| `backend/services/intent.py` | 146 | `import re` | 每次调用 `_extract_budget` |
| `backend/services/question.py` | 171 | `import random` | 每次调用 `generate_question` |
| `backend/services/need_analysis.py` | 147 | `import random` | 每次调用 `_generate_question` |

## 出现原因

开发时在函数内写 import 方便快速测试（不用滚动到文件顶部），提交时忘记移到模块级。

## 解决方案

将 4 处 import 移到各自文件的顶部（与其他 import 放在一起）。

**注意**: Python 有 import 缓存机制，重复 import 几乎零开销，所以这不是性能问题，只是代码规范问题。

## 影响面

- 功能影响：无。Python 缓存 import，移动位置不影响行为
- 测试影响：无
- 风险等级：零

## 验证方法

1. 运行现有测试：`pytest tests/ -v`
2. 确认导入顺序正确（标准库 → 第三方 → 本地）

## 相关文件

- `backend/models/domain.py` — 移 `import re` 到顶部
- `backend/services/intent.py` — 移 `import re` 到顶部
- `backend/services/question.py` — 移 `import random` 到顶部
- `backend/services/need_analysis.py` — 移 `import random` 到顶部
