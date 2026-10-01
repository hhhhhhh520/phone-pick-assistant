# 存储字段单位截断（1TB 显示为 1GB）
> 创建时间: 2026-10-01 | 状态: 🟢已解决（数据 3 行 + 展示层两处 + 前端/后端格式化）

## 问题描述

历史数据清洗把 "1TB" 截断为整数 1（GB 口径），小米13/14/15 Ultra 三款 `storage=1`，
前端按 `${storage}GB` 渲染成"存储: 1GB"。2026-09-30 端到端实测对比/推荐卡片发现。

## 出现原因

TEXT→INTEGER 清洗时只取数字前缀、丢弃单位（与 2026-06-28 RAM/电池清洗同批惯例），
"1TB"→1。同批还产生 storage 列疑似 RAM 误植值。

## 解决方案（2026-10-01）

**数据侧**（单事务 3 行，乐观锁 `WHERE id=? AND storage=1` + rowcount 断言）：
1211 小米13 Ultra / 1213 小米14 Ultra / 1215 小米15 Ultra：`1 → 1024`（GB 口径）
→ 同窗口重导出 phones_export.json。

**展示侧**（统一口径，≥1024 整数倍转 TB）：
- 前端共享 `frontend/src/utils/format.ts` 的 `formatStorage`：1024→"1TB"、128→"128GB"、空→"-"
- `PhoneCard.tsx:170` 与 `CompareTable.tsx:43` 改用 `formatStorage`（CompareTable 的共用 `formatUnit` 不动，其余字段仍走原逻辑）
- 后端 `recommend.py` 新增 `_format_storage`（LLM prompt 镜像格式化，避免"存储: 1024GB"进 prompt）

**守卫测试**：
- `tests/test_storage_unit_fix.py`：真实库 3 款 + export 同步断言 + `_format_storage` 单元（共 6 用例）
- 前端 `format.test.ts`（formatStorage 7 用例，含 0→`-`）+ PhoneCard 3 用例 / CompareTable 2 用例（1TB/GB/缺失）

**范围声明**：storage 列另有 **22 行疑似 RAM 误植值**（8/12/16/18/24），本次不动 → 遗留。

**回滚配方**：字段级 `UPDATE phones SET storage=1 WHERE id IN (1211,1213,1215)`；或以提交前 git HEAD 的 `phones_export.json` + `scripts/import_phones_json.py` 整体还原（该前态含 W1 处理器修复，是干净回滚点。注意：W1 的 DB 备份虽含 storage=1，但整文件回滚会连带撤销 W1 的 9 款处理器修复，勿用作 W2 回滚点）。

## 遗留事项

1. storage 疑似 RAM 误植 22 行（含 ROG 5s Pro storage=18）待人工核对清洗
2. 完整聊天链路 E2E 复验卡片 "存储: 1TB" 被外部阻塞：
   - LLM 订阅 `InvalidSubscription`（阿里云账户 2123047324）——应用已降级兜底，恢复订阅后需复测
   - 前端因 5173 被僵尸进程（PID 19476）占用而起在 5174，origin 不在后端 CORS 白名单 → 预检 400。与 W2 无关，重启前端时可清僵尸进程
3. 根因脚本未堵：`clean_screen_storage.py` 的 `extract_number` 单位盲（`'1TB'→1`）。今日重跑因 storage 列已无数值文本为 no-op，但未来导入文本值会复发——建议加守卫（storage 列出现非数值文本即失败）
4. 派生标签未回填：1211/1213/1215 现满足 `storage>=512` 规则但 features 缺"大存储"标签（仅入 LLM prompt、不参与检索排序）——改了影响 tag 规则输入的数据后需重跑 `backend/data/feature_tags.py`
5. 前端 `formatStorage` 与后端 `_format_storage` 为镜像实现（0 值语义已统一为"缺失"：前端 `-`、后端省略字段），长期防漂移可用共享契约测试表（两侧断言同一组输入→期望元组）

## 相关文件

- `backend/data/phones.db`（3 行修复，gitignore）
- `backend/data/phones_export.json`（同步重导出）
- `frontend/src/utils/format.ts`（新，formatStorage）
- `backend/services/recommend.py:76-97`（_format_storage + 接线）
- `frontend/src/components/PhoneCard.tsx` / `CompareTable.tsx`
- `tests/test_storage_unit_fix.py`、`frontend/src/test/format.test.ts` 等