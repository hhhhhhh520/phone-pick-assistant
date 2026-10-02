# 手机选购助手 - 项目进度

> 创建时间: 2026-04-28 | 最后更新: 2026-10-02（品牌去重 + Xperia 重复行清理，ISSUE-050）

## 项目概述

**项目地址**: D:\my project\phone-pick-assistant
**技术栈**: FastAPI + React 19 + DeepSeek API + SQLite
**当前状态**: 功能完成，代码质量优化中

---

## 当前待办

| 优先级 | 任务 | 说明 | 相关 Issue |
|--------|------|------|-----------|
| P2 | chat.py 架构重构 | 120 行业务逻辑拆分为 ChatOrchestrator | ISSUE-032 |
| P2 | 中文 Prompt Injection 防御 | 当前仅英文正则，中文注入绕过 | REVIEW_REPORT C8 |
| P2 | 补充 sensor_main/telephoto_type 数据 | 仅 26 款旗舰有精确数据，327 款缺 | — |
| P6 | 补充 processor 数据 | 286 条缺失，需外部数据源 | — |
| P6 | 补充 camera_main 数据 | 324 条缺失，需外部数据源 | — |

## 2026-10-02 品牌去重 + Xperia 重复行清理（ISSUE-050）

model 已含品牌前缀时 `f"{brand} {model}"` 输出"真我 真我Neo8"（LLM prompt/匹配结果/aria-label 全中）；
索尼 Xperia PRO-I 同机 3 行。

### 修复
- 横切统一入口：`domain.Phone.display_name`（model 含品牌则原样保留上下文，否则拼一次）；
  前端镜像 `utils/formatPhoneName`（同语义）
- 接入 7 处：recommend ×2 + model_parser ×1 + PhoneCard aria/alt ×2 + **CompareTable 表头 ×2**
  （表头为审查发现的漏网——初版 grep 漏 `phone1.` 形态）；
  chat.py:227（匹配 haystack）与 image_loader（映射键）审查后刻意不动
- 重复行：保留 1233（W1 修复后芯片正确、名干净），删 1738/1748
  → DB 353→351、price<=0 归零、API/DB 口径差消失
- 守卫测试 17 用例先红后绿（后端 10 + 前端 7，含 model===brand 的 vivo/vivo 等值边角）；
  存量测试订正（test_model_parser 原断言锁死 bug 行为 → 改去重期望+反断言；MockPhone 桩同步）
- 353→351 计数同步 3 处（README/CLAUDE.md/export 脚本 docstring）；总行数断言区间化

### 遗留（见 ISSUE-050）
1514 (vivo,vivo) 等 3 行数据本身待人工核对；一次性脚本失效键（重跑 no-op）；
爬虫字段直入 prompt 无净化（两轮审查标记，建议单开工单）；aria 落无 role 元素（预存在）

### 验证
后端 872 全绿（+10）、前端 156 全绿（+7）、build 通过；export 同步 351 行。

---

## 2026-10-02 追问内部 code 防泄漏（ISSUE-049）

追问卡片标题曾渲染"关于brand_not_match_features的追问"——前端 typeNames 5 个旧语义键与
后端 PAIN_POINT_TEMPLATES 6 个 code 零交集 + 兜底透出原值，实际 100% 泄漏。

### 修复
- `MessageItem.tsx`：映射表补全后端全集 6 键（语义对齐模板 description），
  兜底改通用文案"偏好确认"（未知新 code 也不泄漏）；旧语义键保留（后端从未发出，回归覆盖）
- **同批次 severity 徽标修复**（三路审查独立发现的同病灶）：severityLabels/Colors 只映射
  mild/moderate/severe，而后端实际发 high/medium/low → 徽标从未渲染过；补全实际枚举
- `types/index.ts` 两行字段注释同步
- 守卫测试 7 用例（code 泄漏 4：逐键断言专属标签 + 兜底替身反断言；severity 3），
  先红 3 failed 后绿
- 附带核查占位符链路：唯二含 `{brand}` 等占位的分支均 `.format()` 传参完整，无泄漏无 KeyError

### 验证
后端 862 全绿（无改动）、前端 149 全绿（+7）、build 通过；EOF 换行补齐。

---

## 2026-10-01 修复存储字段单位截断（ISSUE-048）

历史清洗把 "1TB" 截断为 1（GB 口径），小米13/14/15 Ultra 三款显示"存储: 1GB"。

### 修复
- 数据：单事务 3 行 storage 1→1024（乐观锁 + rowcount 断言）→ 同窗口重导出 export JSON
- 展示：新增前端共享 `utils/format.ts` 的 `formatStorage`（≥1024 整数倍转 TB），
  PhoneCard/CompareTable 两处接入；后端 recommend.py 新增 `_format_storage` 镜像（LLM prompt 侧）
- 守卫测试：后端 `test_storage_unit_fix.py`（6 用例：数据 3 + export 同步 + _format_storage 单测）、
  前端 format.test.ts（7，含 0→`-`）+ PhoneCard 3 / CompareTable 2

### 遗留（见 ISSUE-048）
storage 疑似 RAM 误植 22 行（8/12/16/18/24）待核对；完整聊天 E2E 被外部阻塞——LLM 订阅
InvalidSubscription（阿里云账户 2123047324，应用已降级兜底）+ 前端 5173 被僵尸进程占用起在 5174 致 CORS 预检 400

### 验证
后端 862 tests 全绿（+6 存储守卫）、前端 142 tests 全绿（+12）；API `/api/phones/1213` storage=1024；
组件级渲染测试直接证明卡片/对比表显示 "1TB"。

---

## 2026-09-30 修复处理器字段代际污染（ISSUE-047）

端到端实测（真启动 + 浏览器对话）发现 21 款机型 processor 被写成"骁龙8 至尊版 Gen5"（全库最高跑分档），含代际不可能机型（小米12 Pro 2021=骁龙8 Gen 1 等）。污染值扭曲游戏/性能排序——实测小米12 Pro ¥1859 顶进"预算3000打原神"推荐前三。

### 修复
- **A桶 9 款**按 id 逐行锁定（乐观锁 + 单事务 + rowcount 断言）回填核实芯片；B桶 5 款（Gen5 为真实芯片）与 C桶 7 款（泛化名存疑）保留
- enrich_camera_data 重算 camera_score 缓存（恰 9 行，小米14 Ultra 90→85 为预期回落）→ 同窗口重导出 phones_export.json
- 新增守卫测试 `tests/test_processor_generation_fix.py`（先红 10 failed → 后绿）
- 备份：`backups/phones.db.bak-before-processor-fix-20260930`

### 遗留（见 ISSUE-047 文末）
B桶芯片命名口径混杂（17 Pro 写第一代至尊版）、C桶存疑机型待人工核对、standardize_processors.py Step 2 模糊归一化待降级为精确匹配（精确键下现幂等，对非常规值有脆弱性）、fill 类脚本缺"只填 NULL"守卫

### 验证
后端 856 tests 全绿（原 846 + 新增 10）；污染计数 21→12（B/C 桶保留）；总行数 353 不变；重启服务后实测"预算3000打原神"小米12 Pro 跌出推荐。

---

## 2026-09-13 修复 38% 手机图片不显示（ISSUE-046）

### 问题

数据库 352 条 `image_url` 里 **132 条（38%）是 Windows 反斜杠写法**（`images\x.jpg`）。
前端拼 URL 时 `API_BASE` 结尾没有 `/`，而 `encodeURI` 不会把 `\` 规范成 `/`（编成 `%5C`），
于是拼出 `http://localhost:8002images%5C...` —— **主机名被吃成 `localhost:8002images`**，
浏览器直接拒绝解析、**连请求都不发**，静默换成默认图标。

### 修复

| 方向 | 内容 |
|---|---|
| 前端容错 | `PhoneCard.tsx` 的 `getFullImageUrl` 提取导出（便于单测）并归一化：`\`→`/`、路径补前导 `/`、基址去尾 `/` |
| 数据归一 | 执行**早已存在但从没跑过**的 `backend/data/fix_image_urls.py`：`Total fixed: 132`，残留反斜杠 132 → **0**，`/images/` 开头 43 → 175 |
| **可持续性** | 审查发现活库 patch 不够：被 git 跟踪的恢复数据源 `phones_export.json` 仍是脏的，恢复脚本裸写 `imageUrl` → **恢复一次 bug 就复发**。补了两层：① `Phone` 模型加 `@validates("image_url")`（覆盖**所有**写入路径）；② `phones_export.json` 132 条归一（diff 恰好 132 行增删） |

⚠️ 该脚本直接跑会 `ModuleNotFoundError`（没把项目根加进 `sys.path`），需 `PYTHONPATH=. ` 前缀。

### 测试

- 前端：`PhoneCard.test.tsx` 新增 `describe('getFullImageUrl')` 5 条，用 **id=1482 的真实值**做样本；
  前端全量 130 passed（12 文件），`tsc -b` 通过
- 后端：新增 `tests/test_image_url_normalization.py` 11 条（模型归一化 + **数据源 JSON 无残留反斜杠**）；
  后端全量 **846 passed**（原本 844 + 11）
- 浏览器 A/B：三条真实反斜杠记录，修复前拼法 `Failed to parse URL`、修复后 **200**

**关于"先证明会红"的更正**：本节初稿写"前端 5 条全红"，但那是因为函数**还没导出**——
import 拿到 undefined 直接抛错，把这个 import 错误当成了红。审查者保留导出、只回退函数体后复测：
**真正有判别力的只有 2 条**（反斜杠归一、斜杠数量），另外 3 条用坏算法也照样绿。
教训：**"红"必须来自被测量的行为，不能来自 import 错误。**

**诚实的边界**：数据归一之后，真实数据里已无反斜杠值，
前端那条容错分支不会再被触发 —— 该分支只有单测守卫（样本是真实历史值）。
DB 清洗为首次执行，执行前已备份到 `backups/phones.db.bak-before-ISSUE046-20260913`（gitignore 内）。

### 附带发现（未处理）

`frontend/.env.example` 写 `VITE_API_BASE=http://localhost:8000`，而组件 fallback 与后端实际都是 8002 ——
**照抄 example 建 `.env` 反而会连不上**。（与面试助手 ISSUE-007 同类的端口约定散落问题。）

## 2026-09-06 系统化场景矩阵测试 + 4 项修复

新增可复用的端到端冒烟工具 `scripts/e2e_scenario_matrix.py`（31 项断言：6 场景×预算符合性+排序正确性、多轮完整流、对比边界、恶意输入，需真实 LLM）。首轮 27/31，暴露 4 个真问题，全部修复后**连跑两遍 31/31**。

### 矩阵暴露的问题与修复

| # | 问题 | 修复 |
|---|------|------|
| 1 | **注入变体漏网**："ignore all previous instructions"（中间多词）绕过正则 | security.py 补变体模式（ignore the previous/disregard/forget 等），配 6 个变体测试 |
| 2 | **对比匹配对空格敏感**：库内 "HUAWEI Mate 60" 匹配不到用户说的"华为Mate60"，三款对比仅找到 1 台 | retrieval.get_phones_by_model 增加去空格归一化子串匹配（优先级2/3 各一层） |
| 3 | **filter 意图被追问拦截**："只看华为，预算三千以内"因缺"游戏需求"维度被追问而非出列表 | chat.py：filter 与 compare 同等跳过完整性追问 |
| 4 | **预算语义解析缺陷**："三千以内"被解析成 ±500 区间（丢了上限语义）；LLM 路径无 filter 判定指引、预算语义表不全 | intent.py：兜底正则识别"千+以内/以下"；INTENT_PROMPT 补预算语义表（以内/以下/到/以上）和 filter 判定要点 |

### 测试

- 新增 `tests/test_matrix_findings.py`（11 个测试：注入变体/空格归一化/filter 直通/预算语义）
- 后端 835 tests 全过；矩阵连跑两遍 31/31

### 遗留观察（不修）

- LLM 意图提取有固有随机性（同句式偶尔判定不同），prompt 语义表已尽量收敛；兜底规则层是确定性的
- R3 多轮中"预算1000-2000+玩游戏"推荐了小米12 Pro（1859元）等老机型——游戏场景按跑分排序在千元档的合理结果，属数据代际问题

---

## 2026-09-06 拍照推荐排序修复 + 影像数据补全

**问题**（试用"预算三千左右拍照"实测发现）：拍照场景按**裸像素降序**，1.08亿像素的 2021 年代老机型（骁龙870）压过 2025-26 年的 5000万大底新机；同时该价位带 0 款有影像标签，tier-1 检索恒为空、降级提示必现。

### 修复

| # | 内容 | 改动 |
|---|------|------|
| 1 | **芯片算力分按安兔兔跑分分档**：此前按芯片名精确匹配配置表，匹配不到一律 10/30（"骁龙8 至尊版 Gen5"跑分 244 万全场最高却被冤枉）；跑分匹配自带年代惩罚，老芯片自然靠后 | camera_score.py |
| 2 | **拍照排序键**：影像评分 → 像素 → 影像标签 → 价格（此前裸像素唯一键） | retrieval.py |
| 3 | **评分缓存入库**：camera_score 列 353 款全量计算入库（此前几乎全空） | enrich_camera_data.py |
| 4 | **影像标签下放**：主摄≥1亿 或 有明确传感器型号 → features 加"影像"（零编造规则），2500-3500 档标签机型 0→7 款，tier-1 恢复命中 | enrich_camera_data.py |

### 效果对比（同一场景"预算三千左右，喜欢拍照"）

| | 修复前 | 修复后 |
|---|--------|--------|
| 第1推荐 | 荣耀500 Pro（2亿像素但影像系统平平） | **小米13 Ultra**（徕卡+一英寸主摄+双长焦，评分90） |
| 第2推荐 | Moto Edge S Pro（骁龙870老机，裸像素凑数） | 荣耀500 Pro |
| 降级提示 | 必现"未找到完全匹配「拍照」" | **消失**（tier-1 命中） |

### 明确不做（数据诚实边界）

- sensor_main/telephoto_type/has_ois：无可靠数据源，**不编造**（camera_telephoto 列 353 款全空）；评分服务对这些缺失给保守分
- 已知偏差：无传感器数据的新机（如 vivo S30 Pro）进不了 tier-1 池，修复依赖后续影像数据采集（PROGRESS 遗留 P2 待办）

### 测试

- 新增 `tests/test_camera_ranking_fix.py`（13 个：跑分分档/老机出局回归/标签幂等）
- 更新 2 个旧像素排序断言为评分语义（test_scenario_matching / test_data_completeness）
- 后端 820 tests 全过；真实服务同场景复测通过

---

## 2026-09-06 LLM 切换火山方舟（Anthropic 协议适配器）

DeepSeek 账户欠费后，切换到火山方舟编程套餐。**注意：方舟编程套餐 key（ark-xxx）只支持 Anthropic 协议**（OpenAI 兼容端点 /api/v3 会报 AuthenticationError），实测可用端点为 `https://ark.cn-beijing.volces.com/api/plan/v1/messages`，模型名 `ark-code-latest`（Claude Code 配置里的 `[1m]` 后缀是上下文标注，不带）。

### 改动

| 项 | 内容 |
|----|------|
| llm.py | 新增 Anthropic Messages 协议适配器：SSE 解析只放行 text_delta（**thinking 增量过滤**）；system 消息拆为顶层字段；相邻同角色消息合并（Anthropic 协议要求）；health_check 双协议分支 |
| config.py | 配置字段 `DEEPSEEK_*` → 中性 `LLM_*`，新增 `LLM_API_PROTOCOL`（openai \| anthropic），DeepSeek 用户改回 .env 即可切回 |
| .env | 接入 Ark（LLM_MAX_TOKENS 提到 4096，思考过程占用输出预算） |
| CI | 测试已离线化，DEEPSEEK_API_KEY secret 依赖移除（dummy key 过必填校验） |

### 验证

- 后端 810 tests 全过（新增 14 个适配器测试：SSE 解析/消息合并/负载构建/协议分发/字段迁移）
- 真实服务冒烟：/health `healthy`（llm available, ark-code-latest）；完整推荐流程 SSE 正常，输出含推荐列表/需求引用/潜在不足，thinking 零泄漏，tier-2 回退 notice 正常触发
- 实测后端模型为 glm-5-3-flash（方舟套餐路由）

---

## 2026-09-06 审查遗留问题批量修复（15 项 + 2 个新发现）

对前几轮审查报告中"标了该修但未修"的项 + 本轮新发现的问题做批量修复。后端 796 tests + 前端 125 tests 全过，`npm run build` 修复后可用，真实服务冒烟通过。

### 重要发现：测试套件此前依赖 DeepSeek 账户余额

19 个测试（chat_route/chat_flow/errors）会打真实 LLM API。**2026-09-06 当天 DeepSeek 账户余额耗尽（402 Insufficient Balance），这 19 个测试全部变红**。顺带暴露一个生产 bug：intent.recognize 的 `await self.llm.chat(...)` 没有 try/except，LLM 不可达时 `/api/chat` 直接 503，"规则兜底"只在 JSON 解析失败时生效。

### 修复清单

| # | 修复 | 改动 |
|---|------|------|
| A | **LLM 不可达降级**：网络错误/402/超时自动走规则兜底，/api/chat 始终 200 SSE（真实服务冒烟验证） | intent.py |
| B | **测试套件离线化**：conftest 新增 `offline_llm` autouse fixture 阻断 chat_stream 真实调用，套件 24.9s→2.3s 且不再依赖账户余额 | conftest.py |
| C | **重写 19 个失效 mock**：`patch("chat.IntentService")` 对 DI 单例无效（历史全靠真实 API 通过），改用 FastAPI `dependency_overrides` | test_chat_route.py, test_errors.py |
| D | **INTENT_PROMPT 预算示例值 10000→100000**：此前示例与规则矛盾，LLM 照抄会静默过滤掉万元以上 17 款机型并跳过追问 | intent.py |
| E | **红米品牌独立映射**：兜底路径此前把"红米"映射成"小米"，丢失全部 20 款红米 | intent.py |
| F | **注入检测不回显命中内容**（H8）：防止攻击者探测规则库 | security.py |
| G | **去掉入站 html.escape**：转义污染 LLM 上下文和"引用原话"功能；XSS 由 React 输出转义负责 | security.py |
| H | **/api/phones 限流 60/min**（H5）：防全库爬取 | phones.py |
| I | **sqlite URL 锚定项目根**：此前相对 CWD 解析，错误目录启动会静默新建空库（根目录现存 2 个 0 字节假库为证），/health 照常通过 | config.py |
| J | **移除死配置 max_message_length**（与 security 的 2000 矛盾且无人引用） | config.py |
| K | **日志轮转 + httpx 降噪**：FileHandler→RotatingFileHandler(10MB×3)，httpx 降到 WARNING（此前每次 LLM 调用打印上游 URL） | main.py |
| L | **retrieval.py 孤儿死代码清理**：ISSUE-036 删 get_all_phones 时漏删的方法体 | retrieval.py |
| M | **前端清理**：删除未用 getPhones/getPhone、生产 console.log；组件卸载中止流式请求；camera 类型补齐后端 5 个影像字段；修复存量 build 报错（CompareTable.test null 类型、PhoneCard.test 未用 import）——**`npm run build` 此前就是坏的** | frontend/src |
| N | **数据资产备份进 git**：新增 export/import 脚对，phones_export.json（295KB/353 款）入 git；恢复演练通过（导出→重建→再导出逐字节一致） | scripts/ |
| O | **仓库卫生**：删除 2 个 0 字节假 phones.db；3 个 missing_data_report*.csv 移出版本控制（.gitignore 早已声明却一直被跟踪） | — |

### 新发现并修复的数据质量问题

| 列 | 脏数据 | 处理 |
|----|--------|------|
| screen_size | 129 条爬虫残留（'6.75英寸纠错'、'6.67英寸主屏分辨率：1604x720px'）| 119 条提取数值 + 10 条置 NULL（clean_screen_storage.py） |
| storage | 5 条（'256GB'、'未知'） | 3 条提取数值 + 2 条置 NULL |

### 新增测试

- `tests/test_review_fixes_0906.py`：17 个针对性测试（LLM 降级、红米检索端到端、限流 429、URL 锚定、死代码清理等）
- test_security.py 新增注入不回显测试；test_chat_route/test_errors 重写为真正生效的 mock

### 待办更新

- ~~REVIEW_REPORT H5/H8~~ 已修；中文注入防御（C8）维持"暂不做"决策
- **提醒：DeepSeek 账户余额已耗尽，线上 LLM 功能当前处于规则兜底降级模式，需充值恢复**

---

## 2026-07-02 无头浏览器实测 + 10 项修复（ISSUE-036~045）

用 Playwright MCP 对 36 个场景做端到端实测，发现 10 个问题，安全审查方案后全部修复。后端 775 tests + 前端 125 tests 全过。

### 修复清单

| ISSUE | 修复内容 | 改动文件 |
|-------|----------|----------|
| 036 | 拍照推荐回退失效：新增 `search_with_fallback` 分级回退（保留预算+场景排序），拍照关键词扩展"影像/潜望长焦/大底"，新增 notice SSE 事件 | retrieval.py, chat.py, types/index.ts, ChatWindow.tsx, MessageItem.tsx |
| 037 | 对比表 null 拼接：CompareTable 加 `formatUnit` 格式化函数，null 显示"-" | CompareTable.tsx |
| 038 | 品牌名重复：PhoneCard 加 `displayModel` 去重 + null guard | PhoneCard.tsx |
| 039 | 对比虚构型号静默回退：型号找不到时不调 `compare([])`，发 notice 提示"未找到机型" | chat.py |
| 040 | 本地图片+号404：`getFullImageUrl` 加 `encodeURI().replace(/\+/g,'%2B')`，防双重编码 | PhoneCard.tsx |
| 041 | 列表/详情字段契约不一致：PhoneBrief 加 imageUrl 字段 | schemas.py, phones.py |
| 042 | /health 阻塞 1.66s：改后台异步刷新 LLM（`refresh_llm_health_periodically`），请求读缓存，HTTP 永远 200 | main.py |
| 043 | 排序参数未实现：list_phones 加 `sort` Query（pattern 校验），order_by 升/降序 | phones.py |
| 044 | PhoneCard onClick 未接线：去除 role=button/tabIndex/onKeyDown/onClick 交互伪装 | PhoneCard.tsx, MessageItem.tsx |
| 045 | 末尾空气泡：bottomRef 锚点加 `aria-hidden` + `height:0` | MessageList.tsx |

### 安全审查纠正的关键错误

- 方案2 保留 camelCase（不改 image_url），避免 213 款图片全失效
- 方案2 保留 to_dict 嵌套结构，避免 CompareTable 崩溃
- 方案1 compare 空列表走独立路径，避免 LLM 幻觉
- 方案5 /health 保持 HTTP 200，避免触发容器重启循环

---

## 2026-06-25 全面代码审查

使用 5 个并行专项审查 Agent（Critical Pass、Security、Performance、Testing、Maintainability）对全量代码库进行多角度审查。

**审查结果**: 原始发现 41 个 → 验证后真实问题 17 个（排除 5 个假阳性）

### 已修复（9 项，759 tests passed）

| ISSUE | 修复内容 | 改动 |
|-------|----------|------|
| 027 | 删除 `recommend.py` 中 3 处 `print("[DEBUG]")` | 删除 3 行 |
| 028 | 删除 `chat.py` 中重复的 cons 后处理逻辑 | 删除 16 行 |
| 029 | 抽取 `_find_matching_key` 公共方法消除 antutu 函数重复 | 重构 ~120 行 |
| 030 | 抽取 `_parse_json_field` 静态方法消除 to_dict 重复 | 重构 ~40 行 |
| 031 | 4 处 `import re/random` 从函数内移到模块级 | 4 个文件 |
| 033 | 删除 `ChatErrorBoundary` + `is_production` 死代码 | 2 个文件 |
| 035 | CORS 从 12 个 localhost 简化为 2 个 | config.py |
| — | `_extract_budget` 正则 bug（"X万以下" 匹配失败） | intent.py 2 行 + 12 测试 |
| — | `test_logging.py` 方法名过时（`_call_api` → `chat`） | test_logging.py 1 行 |

### 假阳性（不是问题）

| 原始发现 | 原因 |
|----------|------|
| `question.py:189` IndexError | 受调用方 `question.py:271` 的守卫保护 |
| `llm.py` tiktoken 每次探测 | Python import 缓存，非热路径 |
| `llm.py` httpx 每次新建客户端 | `async with` 是 httpx 正确用法 |
| `dependencies.py` 单例竞态 | FastAPI 单线程事件循环 |
| `session.py` 模块级全局状态 | FastAPI 单例服务标准做法 |

---

## 2026-06-28 多维度审查 + 数据修复

5 个并行 Agent（代码质量、安全、数据质量、前端契约、测试覆盖）从不同角度审查，发现 42 项 → 验证后 6 个真问题 → 修复 5 项。

### 审查结果（详见 REVIEW_REPORT.md）

| 维度 | CRITICAL | HIGH | MEDIUM | LOW |
|------|----------|------|--------|-----|
| 安全 | 1 | 3 | 3 | 2 |
| 数据质量 | 5 | 5 | 7 | 3 |
| 前端契约 | 2 | 0 | 6 | 5 |

### 已修复（5 项，764 tests passed）

| # | 修复内容 | 改动文件 |
|---|----------|----------|
| C5 | 疼痛点字段发送：question SSE 事件包含 pain_point_type/severity | chat.py |
| C6 | SSE 错误处理：前端添加 error 事件分支，不再显示空白气泡 | ChatWindow.tsx |
| C1 | RAM 数据清洗：101 条文本 → 98 提取 + 3 NULL | phones.db |
| C2 | 电池数据清洗：121 条文本 → 120 提取 + 1 NULL | phones.db |
| C3 | 影像字段补全：26 款旗舰精确匹配 + 327 款品牌默认值 | phones.db |

### 假阳性（排除）

| 原始发现 | 原因 |
|----------|------|
| 3 个重复型号 | 数据库查询为 0，Agent 用了过时数据 |
| LLM 错误泄露 API 详情 | 已在 06-27 修复（commit 0a18172） |
| /health 信息泄露 | 已在 06-27 修复（60 秒缓存） |

### 不修复（经讨论确认）

| 问题 | 原因 |
|------|------|
| 品牌映射（小米/红米合并） | 分开是合理设计，合并反而丢失精度 |
| 中文 Prompt Injection | 正则误杀率太高，需 LLM 语义判断 |

### 新增文件

- `backend/data/clean_ram_battery.py` — RAM/电池数据清洗脚本
- `backend/data/fill_camera_fields.py` — 影像字段补全脚本
- `REVIEW_REPORT.md` — 完整审查报告（42 项发现）

---

## 2026-06-28 功能测试验证（TEST_CHECKLIST.md）

基于代码探索生成 266 个测试点的完整测试清单，启动项目进行实际验证。

### 测试结果

| 类别 | 测试数 | 通过 | 说明 |
|------|--------|------|------|
| 后端 API（curl） | 30 | 28 | 2 项为已知数据限制 |
| 前端界面（Playwright） | 8 | 8 | 核心交互全部通过 |

### 已验证功能

- API 基础端点：根路径、健康检查（含缓存）、手机列表/详情/过滤/分页
- Chat 接口：新会话、追问模式、推荐模式、对比模式、SSE 事件格式
- 多轮对话：完整追问流程、画像重置、否定需求处理、快捷回复交互
- 前端界面：欢迎页、消息显示、手机卡片、对比表格、搜索历史
- 安全：Prompt 注入防护（拒绝执行，不泄露系统提示词）

### 发现的数据质量问题（D1/D2 已在后续修复）

| # | 描述 | 严重程度 | 状态 |
|---|------|----------|------|
| D1 | RAM 字段含多余文字 | 低 | ✅ 已修复（2026-06-28 数据清洗） |
| D2 | 电池字段重复后缀 | 低 | ✅ 已修复（2026-06-28 数据清洗） |
| D3 | 努比亚小牛 RAM/存储/充电 null | 低 | — |
| D4 | 努比亚小牛重量 "5g"（明显错误） | 低 | — |
| D5 | 对比模式未匹配到用户指定型号 | 中 | — |
| D6 | camera_main 324 条缺失 | 低 | — |

详见 `TEST_CHECKLIST.md`（75 个关键测试点 + 预期结果 + 验证方式）。

---

## 2026-06-27 多维度审查修复（12 项，764+121 tests passed）

5 个并行审查 Agent（架构、安全、前端、API、测试）发现 110 项 → 验证后 13 项真实问题 → 修复 12 项（#8 跳过）

### 已修复

| # | 类别 | 修复内容 | 改动文件 |
|---|------|----------|----------|
| 1 | 架构 | SSE 生成器加 try/except，异常时返回 error 事件 | chat.py |
| 2 | 安全 | 系统提示词改用 system 角色，防止指令泄露 | intent.py, recommend.py |
| 3 | 安全 | /health 缓存 LLM 结果 60 秒，防止 API 额度耗尽 | main.py |
| 4 | 前端 | 6 个组件添加 ARIA 属性（无障碍） | InputBar, PhoneCard, QuickReplyButtons, MessageList, CompareTable, SearchHistory |
| 5 | 前端 | 添加加载指示器（三个脉冲点动画） | ChatWindow, MessageList, MessageItem |
| 6 | 测试 | `assert count == 353` 改为范围检查 `300-500` | test_data_completeness.py |
| 7 | 测试 | 创建 conftest.py 提取共享 fixtures | conftest.py, test_chat_route.py, test_chat_flow.py |
| 9 | API | 手机列表添加 offset 分页参数 | phones.py |
| 10 | API | SSE 错误格式添加 code 字段 | chat.py |
| 11 | 安全 | LLM 错误响应在生产环境隐藏 original_error | main.py |
| 12 | 数据 | 安兔兔 A18/A18 Pro 分数修正 | antutu_scores.json, test_antutu_config.py |
| 13 | 前端 | 消息 ID 改用 crypto.randomUUID() | ChatWindow.tsx |

### 跳过

| # | 原因 |
|---|------|
| 8 | threading.Lock → asyncio.Lock：锁操作微秒级，实际无性能影响；改动需修改 10+ 调用点和 10+ 测试文件，风险大于收益 |

### 验证修复

- 后端: 764 tests passed
- 前端: 121 tests passed
- 测试基础设施修复: rate limiter 双实例问题、health cache 测试隔离问题

---

## 已完成

| 阶段 | 内容 | 完成日期 |
|------|------|----------|
| MVP | 核心功能 9 个任务 | 2026-04-28 |
| 多轮对话 | 5 维度引导追问 + 痛点检测 | 2026-05-06 |
| 数据清洗 | 品牌修复 122 条、删除无效 51 条、RAM/Storage 补充 | 2026-05-02 |
| QA 测试 | 4 Agent 并行测试，5 问题全部修复 | 2026-05-05 |
| P3 改进 | LLM 上下文限制 + Token 估算 | 2026-05-02 |
| P0 改进 | 推荐解释增强 + 用户原话引用 + 潜在不足 | 2026-05-06 |
| P1 改进 | 体验标签库（19 特性 + 13 适用人群） | 2026-05-06 |
| P2 改进 | 痛点追问机制（6 种冲突检测） | 2026-05-06 |
| 安兔兔数据 | 处理器跑分配置化（JSON 文件） | 2026-05-06 |
| 代码审查 | ISSUE-027~031, 033, 035 修复 | 2026-06-25 |
| 测试覆盖 | 后端 chat 路由 16 测试 + 前端 7 组件 84 测试 | 2026-06-25 |
| 死代码清理 | 4 个未使用函数 + 23 个对应测试 | 2026-06-25 |
| 正则修复 | `_extract_budget` "X万以下" 匹配失败 | 2026-06-25 |
| 项目整理 | 23 个 backup DB 删除 + 19 个脚本移入 scripts/ | 2026-06-25 |
| 多维度审查 | 5 Agent 并行审查，42 项发现，验证 6 个真问题 | 2026-06-28 |
| 数据清洗 | RAM 98 条 + 电池 120 条提取，消除 TEXT 垃圾数据 | 2026-06-28 |
| 影像字段补全 | 26 款旗舰精确 + 327 款品牌默认 image_brand | 2026-06-28 |
| 疼痛点修复 | SSE question 事件发送 pain_point 字段，前端 UI 生效 | 2026-06-28 |
| SSE 错误处理 | 前端添加 error 事件分支，错误时显示提示 | 2026-06-28 |

---

## 关键决策记录

| 决策 | 选择 | 原因 | 日期 |
|------|------|------|------|
| LLM 模型 | DeepSeek Chat | 国内可用、性价比高 | 2026-04-28 |
| 流式通信 | SSE | 比 WebSocket 简单，FastAPI 原生支持 | 2026-04-28 |
| 会话存储 | 内存字典 + TTL | 简单可靠，单实例足够 | 2026-04-28 |
| 意图识别 | LLM + 规则兜底 | LLM 准确但可能失败，规则保底 | 2026-05-06 |
| 追问策略 | 5 维度 + 痛点检测 | 覆盖核心需求维度，冲突检测提升体验 | 2026-05-06 |

---

## 启动命令

```bash
# 后端（端口 8002）
cd "D:\my project\phone-pick-assistant"
.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8002

# 前端（端口 5173）
cd frontend
npm run dev

# 测试
.venv/Scripts/python.exe -m pytest tests/ -v
cd frontend && npm test
```

---

## 相关文档

- `README.md` — 项目说明、快速开始
- `docs/TODO-NEXT.md` — 后续待办
- `docs/FORMAL_VERSION_PLAN.md` — 正式版计划
- `issues/` — 问题追踪（ISSUE-001 ~ ISSUE-045）
