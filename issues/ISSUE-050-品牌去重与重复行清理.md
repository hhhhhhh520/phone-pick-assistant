# 品牌重复拼接 + Xperia 重复行清理
> 创建时间: 2026-10-02 | 状态: 🟢已解决

## 问题描述

**问题一（品牌重复拼接）**：model 字段已含品牌前缀时，`f"{brand} {model}"` 直接拼接输出重复品牌。
2026-09-30 端到端实测：S1 推荐列表出现"**真我 真我**Neo8"、S3 对比表出现"**苹果 苹果**iPhone 15"，
且重复名进入 LLM prompt（模型文案原样复读）、推荐匹配结果与前端 aria-label/alt。

**问题二（重复行）**：索尼 Xperia PRO-I 同一台手机在库中 3 行：

| id | model | price | processor | 判定 |
|----|-------|-------|-----------|------|
| 1233 | Xperia PRO-I（干净名） | 10999 | 骁龙888（W1 已修复） | **保留** |
| 1738 | 索尼Xperia PRO-I高通骁龙888（爬虫垃圾名） | 10999 | 骁龙888 | 删除（重复） |
| 1748 | 索尼移动Xperia Pro-i | **0** | 骁龙8 Gen 1（PRO-I 实为888，错） | 删除（价格0对 API 不可见 + 芯片错） |

## 出现原因

- 展示层无判重直接拼接（后端 3 处、前端 2 处各自为政）
- 爬虫多轮收录同机型（不同命名形态）形成重复行；price=0 行被 `phones.py:30` 的
  `price > 0` 过滤造成 API 352 vs DB 353 的口径差

## 解决方案（2026-10-02）

**去重 helper（横切统一入口）**：`domain.Phone.display_name` 属性——model 已含品牌前缀
则原样使用（**保留品牌上下文**，LLM prompt 需要），否则 `brand + model` 拼一次；
与前端 PhoneCard.displayModel 同思想（前端展示品牌行+去重型号行分离，语义各自成立）。

**接入点（7 处）**：
- 后端 3：`recommend.py` prompt 首段与 cons 行、`model_parser.py` 匹配结果
- 前端 4：`PhoneCard.tsx` aria-label 与 alt、`CompareTable.tsx` 两个表头
  （表头为三路审查中的攻击者视角发现——初版盘点 grep 漏匹配 `phone1.` 形态，
  S3 实测引用的"苹果 苹果iPhone 15"症状在表头，已修；统一走
  `utils/formatPhoneName`，与后端 display_name 同语义。
  PhoneCard 的 displayModel（剥离品牌）仍用于 h3 分行展示，用途不同）

**刻意不动**（审查确认）：`chat.py:227` 匹配 haystack（拼接用于子串包含判定，改动会变匹配行为）；
`image_loader/update_images` 的 `brand model` 是映射键非展示；日志/打印类。

**重复行删除**：保留 1233，事务删除 1738/1748（model 匹配 + rowcount 断言）
→ DB 353→**351**、price<=0 归零、**API 与 DB 口径差消失**（352 vs 353 之谜闭环）。
保留行决策与 2026-09-30 安全审查的差异说明：审查当时建议保留 1738，因彼时 1233 芯片
仍带污染；W1（ISSUE-047）修复后 1233 芯片已正确且 model 名干净，故改保 1233。

**守卫测试**：`tests/test_display_dedup.py` 10 用例（display_name 5 + 接入点 2 + 去重 3）
+ PhoneCard aria 1 用例，先红 11 后绿。
**存量测试订正**：`test_model_parser.py` 原断言 `"小米 小米14" in result` 把 bug 行为
锁死为契约，订正为去重后期望 + 反断言（`not in`）。`MockPhone` 桩补 display_name 属性
（契约变更需测试双同步）。

## 验证

后端 872 全绿（+10）、前端 150 全绿（+1）、build 通过；export 同步 351 行。

## 遗留事项

1. 索尼块疑似重复行未扩 scope：id=1232 'Xperia'（¥9499 泛化名）、
   id=1747 '索尼Xperia Pro360度天线设计'（爬虫垃圾名）、
   **id=1514 (brand='vivo', model='vivo')**（model=品牌，分行展示会各出现一次"vivo"
   ——属数据本身问题，与前两项同批待人工核对修正）；对比表"型号"行显示含品牌前缀的
   原始 model（如"苹果iPhone 15"）为独立字段展示，非拼接，不改
2. 一次性脚本失效键（审查确认重跑为 no-op 不崩溃，不改）：`standardize_processors.py`
   EMPTY_FILL_MAP 的 id=1748、`supplement_price.py`/`update_camera_data.py`/
   `update_processor_data.py` 中被删 model 名的映射键——重跑时相关补值静默不生效
3. 爬虫字段（brand/model/features/pros/cons）直入 LLM prompt 无净化——**两轮独立审查
   均标记**的既有注入面，非本 issue 引入，建议单开 ISSUE 跟踪
4. 无障碍既有缺陷（非本次引入）：aria-label 落在无 role 的 div 上、DefaultIcon svg
   无可访问名称
5. 静态报告含被删 model 名（`phone_models_cleaned.txt`、`missing_data_report*.csv`）——
   无代码读取，仅报告与库不一致
6. 新增 Phone 展示字段时测试桩（MockPhone 等）需同步实现 display_name

## 相关文件

- `backend/models/domain.py`（display_name 属性）
- `backend/services/recommend.py`、`backend/services/model_parser.py`（接入）
- `frontend/src/components/PhoneCard.tsx`（aria/alt）
- `tests/test_display_dedup.py`（新守卫）、`tests/test_model_parser.py`（桩+断言订正）
- `backend/data/phones_export.json`（351 行同步）；回滚：git HEAD 的 353 行 export + import 脚本
