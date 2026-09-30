# 处理器字段代际污染（21款机型被写入"骁龙8 至尊版 Gen5"）
> 创建时间: 2026-09-30 | 状态: 🟢已解决（A桶9款修复，B/C桶遗留见文末）

## 问题描述

2026-09-30 端到端实测发现：数据库 21 款手机 `processor` = "骁龙8 至尊版 Gen5"（全库最高跑分档 2,449,060），其中包含**发布代际不可能**的机型。污染值作为 camera_score 芯片分档与游戏/性能场景排序的输入，直接扭曲推荐结果——实测"预算3000打原神"场景，小米12 Pro（¥1859，实为 2021 年骁龙8 Gen 1 机型）被顶进推荐前三，且 LLM 推荐文案基于错误芯片编造了"同样搭载骁龙8 至尊版 Gen5 应对原神毫无压力"的理由。

## 出现原因

根因链（git 追溯实证）：
1. 影像/跑分补全批次（commit `276b0f4`、`41998c3`）引入的芯片映射表以 "骁龙8 至尊版 Gen5" 为键（现存于 `backend/data/antutu_scores.json`、`backend/services/camera_score.py:31` 注释）
2. 补全脚本把映射表键写入了 phones.processor 列，且匹配范围未做代际校验，命中了 2021-2024 年的旧机型
3. `standardize_processors.py` Step 2 对全表非空 processor 走 `get_canonical_processor` 归一化。实测其策略 1（精确键）最先执行，库内第一代"骁龙8 至尊版"（现 47 行 = 修复前 45 + 本次回填的 1214/1215）均为跑分表精确键，重跑为 no-op；但策略 5-7 的双向子串模糊匹配对**不在跑分表中的非常规值**仍有误归一风险，建议降级为精确匹配 + dry-run diff（卫生项，见遗留）
4. 856 个测试中无任何断言真实库 processor 值的用例，污染长期存活

## 解决方案（2026-09-30）

**A桶修复（9 款，按 id 逐行锁定 + 乐观锁 + 单事务）**：

| id | 机型 | 修复前 | 修复后 |
|----|------|--------|--------|
| 1114 | ROG 5s Pro | 骁龙8 至尊版 Gen5 | 骁龙888+ |
| 1209 | 小米12 Pro | 骁龙8 至尊版 Gen5 | 骁龙8 Gen 1 |
| 1210 | 小米13 Pro | 骁龙8 至尊版 Gen5 | 骁龙8 Gen 2 |
| 1211 | 小米13 Ultra | 骁龙8 至尊版 Gen5 | 骁龙8 Gen 2 |
| 1212 | 小米14 Pro | 骁龙8 至尊版 Gen5 | 骁龙8 Gen 3 |
| 1213 | 小米14 Ultra | 骁龙8 至尊版 Gen5 | 骁龙8 Gen 3 |
| 1214 | 小米15 Pro | 骁龙8 至尊版 Gen5 | 骁龙8 至尊版* |
| 1215 | 小米15 Ultra | 骁龙8 至尊版 Gen5 | 骁龙8 至尊版* |
| 1233 | Xperia PRO-I | 骁龙8 至尊版 Gen5 | 骁龙888 |

\* 库内字面值为"骁龙8 至尊版"；该芯片世代为 2024.10 发布的第一代至尊版（SM8750），与 2025 世代的"骁龙8 至尊版 Gen5"（SM8850）是两代芯片，为免误读此处不加文字后缀。

执行防护：DB 备份（`backups/phones.db.bak-before-processor-fix-20260930`）→ 停 uvicorn → 逐条 `WHERE id=? AND processor=旧值`（rowcount==1 断言，异常回滚）→ `enrich_camera_data.py` 重算 camera_score 缓存列（恰好 9 行）→ 同窗口重导出 `phones_export.json` → 守卫测试先红（10 failed）后绿。

**守卫测试**：`tests/test_processor_generation_fix.py`（真实库 9 款逐款断言 + export 副本 A 桶干净断言）。

## 遗留事项（不在本次范围）

1. **B桶（5款，Gen5 为真实芯片，现值保留）**：小米17/17 Pro Max/17 Ultra、Redmi K90 Pro、荣耀500 Pro。⚠️ 命名口径混杂：小米17 Pro 反而写第一代"骁龙8 至尊版"，K90 家族（至尊版）与 K90 Pro（Gen5）不一致——建议后续统一芯片命名口径（动前先 grep `standardize_processors.py` 再犯通道）
2. **C桶（7款，泛化名/2026新机无法核实代际，保留原状）**：vivo S50 Pro / S50 Pro mini、vivo 'X'、三星 'Galaxy S'、真我Neo8、Moto Edge / edge
3. **standardize_processors.py Step 2 模糊归一化**：精确键下现为幂等（第一代值均为跑分表精确键），但对不在跑分表中的非常规值有误归一脆弱性——建议降级为精确匹配 + dry-run diff
4. fill 类脚本缺"只填 NULL 不覆盖"守卫

## 相关文件

- `backend/data/phones.db`（修复对象，gitignore）
- `backend/data/phones_export.json`（同步重导出）
- `tests/test_processor_generation_fix.py`（守卫测试）
- `backend/data/standardize_processors.py`（再犯通道，待整改）
- `backups/phones.db.bak-before-processor-fix-20260930`（修复前快照）
