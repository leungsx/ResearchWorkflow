# ResearchWorkflow 分层架构契约

Last updated: 2026-06-30

本文档定义 ResearchWorkflow 的系统边界。目标不是把本地工作流改造成复杂平台，而是让“源材料、加工逻辑、知识资产、浏览界面、质量检查”各司其职，避免链接混乱、重复生成、证据边界不清和长期维护困难。

## 架构原则

1. Markdown 是长期知识源，HTML 是默认阅读界面。
2. 源资产可以人工编辑，生成资产只能由脚本刷新。
3. 用户侧所有可点击本地入口默认打开 HTML，不直接打开裸 Markdown。
4. 每个重要源资产应有可追踪的展示页或明确的不展示理由。
5. 每次自动化运行后必须能通过审计发现断链、裸 Markdown 链接、证据越界和状态不一致。

## 五层边界

| 层级 | 职责 | 典型路径 | 允许人工编辑 | 主要消费者 |
|---|---|---|---|---|
| Source 源材料层 | 保存事实来源、原文、原始导入和可追溯材料 | `library/`, `projects/*/literature/readers/`, `vault/01_Literature/` | 是 | Codex、写作、证据核验 |
| Processing 加工层 | 导入、抽取、推荐、生成上下文包和知识资产 | `scripts/*.py`, `Makefile` | 是 | 自动化任务 |
| Knowledge 知识资产层 | 保存长期论文笔记、概念、方法、项目状态、复习队列和图谱数据 | `vault/02_Concepts/`, `vault/03_Methods/`, `vault/13_Knowledge_Graph/`, `vault/14_Review_Queue/`, `projects/*/*.md` | 是 | Obsidian、Codex、后续写作 |
| Presentation 展示层 | 提供浏览器优先的阅读、复习、导航、搜索和图谱入口 | `study_dashboard.html`, `paper_reading/`, `knowledge_cards/`, `knowledge_graph/`, `search/`, `logs/` | 否 | 用户 |
| Orchestration / QA 编排质检层 | 串联刷新、备份、审计、归档和远程快照 | `make workflow-refresh`, `workflow_health.html`, `backups/`, `codex/` | 部分 | 用户、Codex、自动化 |

## 资产分类

### Canonical Assets

Canonical assets 是可以长期维护和引用的源文件：

- `vault/**/*.md`
- `projects/**/*.md`
- `projects/**/*.yaml`
- `projects/*/project_state.json`
- `library/literature_matrix.csv`
- `vault/13_Knowledge_Graph/*.csv`
- `vault/13_Knowledge_Graph/search_index.json`
- `vault/13_Knowledge_Graph/workflow_state.json`
- `vault/13_Knowledge_Graph/action_queue.json`
- `vault/13_Knowledge_Graph/workflow_audit_report.json`
- `vault/13_Knowledge_Graph/collaboration_state.json`
- `vault/13_Knowledge_Graph/archive_policy.json`
- `vault/14_Review_Queue/review_queue.csv`
- `vault/14_Review_Queue/review_state.json`

这些文件可以人工编辑，也可以由脚本追加或更新。它们是研究记忆和证据状态的来源。

### Generated Assets

Generated assets 是脚本生成的浏览和索引文件：

- `study_dashboard.html`
- `paper_reading/*.html`
- `paper_reading/views/*.html`
- `paper_reading/views/directories/*.html`
- `knowledge_cards/index.html`
- `knowledge_cards/review_today.html`
- `knowledge_cards/views/*.html`
- `knowledge_graph/index.html`
- `search/index.html`
- `logs/index.html`
- `logs/views/*.html`
- `workflow_health.html`
- `workflow_state.html`
- `action_queue.html`
- `project_collaboration.html`
- `archive_policy.html`
- `backups/index.html`

这些文件不应手工维护。发现错误时应修生成脚本或源文件，然后重新运行生成命令。

## 链接契约

所有生成 HTML 页面中的本地链接必须遵守：

1. 指向 Markdown 的链接必须转换为对应 HTML 镜像页。
2. 指向概念卡或方法卡的链接必须转换为 `knowledge_cards/views/*.html`。
3. 指向学习日志的链接必须转换为 `logs/views/*.html`。
4. 指向普通 Markdown 或项目 Markdown 的链接必须转换为 `paper_reading/views/*.html`。
5. 指向文件夹的链接必须转换为 `paper_reading/views/directories/*.html`，除非该文件夹有 `README.md`，则优先展示 README 镜像。
6. 生成页可以显示源文件路径，但不提供裸 Markdown 点击入口。

## 资产清单契约

`vault/13_Knowledge_Graph/artifact_manifest.csv` 是源资产与展示资产之间的索引表，由 `make learning-dashboard` 生成。

推荐字段：

| 字段 | 含义 |
|---|---|
| `source_path` | 源文件或源文件夹相对路径 |
| `source_type` | `markdown`, `directory`, `html`, `csv`, `generated_entry` 等 |
| `display_path` | 用户默认打开的 HTML 或可浏览入口 |
| `display_type` | `paper_page`, `markdown_view`, `card_view`, `log_view`, `directory_view`, `index`, `graph` 等 |
| `title` | 浏览标题 |
| `layer` | 所属架构层 |
| `generated_by` | 生成命令或脚本 |

这个清单的用途：

- 让首页、图谱、日志、项目看板共享同一套展示路径。
- 支持审计脚本检查“源文件是否有展示页”。
- 支持后续搜索、推荐、复习和项目状态判断。

## 命令契约

常用命令职责如下：

| 命令 | 职责 |
|---|---|
| `make obsidian-graph` | 从 Obsidian 双链导出图谱 CSV |
| `make learning-dashboard` | 生成 HTML 展示层和 artifact manifest |
| `make search-index` | 单独刷新 `search_index.json`，通常由 `make learning-dashboard` 自动包含 |
| `make workflow-state` | 单独刷新 `workflow_state.json` 和 `workflow_state.html` |
| `make action-queue` | 单独刷新 `action_queue.json` 和 `action_queue.html` |
| `make collaboration-state` | 单独刷新 `collaboration_state.json` 和 `project_collaboration.html` |
| `make archive-policy` | 单独刷新 `archive_policy.json` 和 `archive_policy.html` |
| `make schema-validate` | 校验核心 JSON/CSV 状态文件的结构、计数和 HTML 入口 |
| `make workflow-audit` | 检查入口、链接、证据边界、备份和生成资产健康 |
| `make workflow-refresh` | 顺序运行图谱、展示、备份、归档和审计 |
| `make workflow-refresh-git` | 在 refresh 基础上提交并推送文本资产 |

## 渲染模块边界

`make learning-dashboard` 的实现应保持如下职责拆分：

| 模块 | 职责 |
|---|---|
| `scripts/build_learning_dashboard.py` | 页面布局、HTML 外壳、各入口页生成顺序 |
| `scripts/rendering/paths.py` | 全局路径常量、标题读取、CSV/Markdown/HTML 基础列表工具 |
| `scripts/rendering/routes.py` | 本地源文件、目录和 Markdown 链接到默认 HTML 展示页的路由规则 |
| `scripts/rendering/manifest.py` | `artifact_manifest.csv` 行生成与写入 |
| `scripts/rendering/review.py` | 从 `review_queue.csv` 生成今日复习状态和复习项展示路径 |
| `scripts/rendering/search.py` | 从 `artifact_manifest.csv` 生成全局搜索索引 |
| `scripts/rendering/workflow_state.py` | 聚合项目、复习、搜索、图谱和审计状态 |
| `scripts/rendering/action_queue.py` | 从总状态生成按优先级排序的开放行动 |
| `scripts/rendering/collaboration.py` | 聚合项目协作分工、用户待确认事项和 Codex 可执行事项 |
| `scripts/rendering/archive_policy.py` | 报告备份、日志、生成资产和缓存文件的归档/清理策略 |
| `scripts/rendering/schemas.py` | 校验核心状态文件 schema、计数一致性和 HTML 入口 |

新增展示入口时，先扩展 `routes.py` 或 `manifest.py`，再由页面生成器调用；不要在页面模板里临时拼接 Markdown 直链。

## 项目状态契约

`projects/<project>/project_state.json` 是给脚本和自动化读取的机器可读项目状态，不替代 `00_project_dashboard.md`、`reading_board.md` 或文献综述工作台。

它应由 `make project-state PROJECT=<project>` 或 `make learning-dashboard` 自动刷新，至少包含：

- 项目元数据：slug、title、status、路径。
- 固定入口：学习仪表盘、今日精读、项目看板、阅读看板、文献综述工作台、artifact manifest。
- 文献状态：矩阵条数、阅读状态计数、全文记录数、Reader 数、上下文包数、最近推荐、最近主读、下一篇候选。
- 质量状态：evidence gate、到期复习数。
- 复习状态：到期数量、逾期数量、7 天内复习数量、今日重点复习项和 HTML 展示路径。
- 展示资产：与项目相关的 manifest 条目摘要。
- 搜索资产：全局搜索页和搜索索引路径，供仪表盘、项目状态和自动化复用。
- 下一步建议：供 fast-lane、每日推荐和仪表盘引用。

## 复习状态契约

`vault/14_Review_Queue/review_queue.csv` 是人工和脚本共同维护的长期复习源表；`vault/14_Review_Queue/review_state.json` 是由脚本生成的今日状态快照。

`review_state.json` 至少包含：

- 今日日期、生成时间和源队列路径。
- 总数、今日到期、逾期、未来 7 天和未排期数量。
- 今日已学习数量，以及当天已完成复习项列表。
- `focus_items`：今天最应该主动回忆的知识卡。
- 每个复习项的源卡片路径和默认 HTML 展示路径。
- `last_reviewed`、`review_count` 和 `learning_status` 用于区分“已学习”和“未处理”；打开 HTML 本身不等于写回复习完成。

用户侧默认打开 `knowledge_cards/review_today.html`，不直接打开 CSV 或 Markdown 卡片。

完成复习后应通过 `make review-studied ID=<review-id>` 或 `make review-studied-due` 写回 `review_queue.csv`。行动队列只应为真正到期且未在当天标记学习的条目生成复习行动。

## 搜索索引契约

`vault/13_Knowledge_Graph/search_index.json` 是由 `artifact_manifest.csv` 派生的机器可读搜索索引；`search/index.html` 是用户侧默认搜索入口。

搜索索引至少包含：

- 标题、源路径、展示路径、架构层、展示类型、项目、日期和权重。
- 每个条目的短摘要、命中片段文本、关键词和用于前端搜索的规范化文本。
- 所有结果的点击目标必须是 HTML 展示页，不直接打开 Markdown 源文件。
- `search/index.html` 应支持相关度排序、项目筛选、展示类型筛选、命中片段和关键词高亮。

搜索层只负责发现和导航，不替代图谱、复习队列、项目状态或证据门禁。

## 工作流总状态契约

`vault/13_Knowledge_Graph/workflow_state.json` 是给自动化读取的总状态快照；`workflow_state.html` 是用户侧浏览入口。

它聚合：

- 核心入口：今日精读、今日复习、知识图谱、全局搜索、工作流体检。
- 计数状态：manifest 条目数、搜索条目数、项目数、Git 待提交路径数。
- 审计状态：最近一次 `workflow-audit` 的 PASS/WARN/FAIL。
- 复习状态：到期数量和重点复习项。
- 项目状态：每个项目的文献矩阵规模、Reader 数、最近主读和下一步动作。
- 下一步建议：按审计失败、到期复习和项目动作排序。

## 行动队列契约

`vault/13_Knowledge_Graph/action_queue.json` 是结构化开放行动队列；`action_queue.html` 是用户侧默认入口。

行动队列应满足：

- 每个行动包含 `kind`、`priority`、`priority_band`、`priority_label`、`priority_reason`、`title`、`reason`、`entrypoint`、`source` 和 `status`。
- `entrypoint` 必须指向存在的 HTML 展示页。
- 优先级层级固定为 `P0` 阻塞写作/投稿、`P1` 今日学习/阅读、`P2` 项目成熟度、`P3` 系统维护。
- 排序先按 `priority_band`，再按数字 `priority`、`kind` 和标题稳定排序。
- 重点知识卡只有在存在真正到期复习时进入行动队列；未来 7 天复习项只在复习页展示，不应提前变成待办。
- 行动队列从 `workflow_state.json` 派生，不替代项目状态、复习状态或审计报告。

## 项目协作层契约

`vault/13_Knowledge_Graph/collaboration_state.json` 是项目协作分工的机器可读状态；`project_collaboration.html` 是用户侧默认入口。

协作层应满足：

- 汇总每个项目的阶段、文献矩阵规模、Reader 数、最近主读和 HTML 入口。
- 把事项区分为“用户待确认”和“Codex 可推进”。
- 用户待确认通常包括 evidence gate 边界、是否补全文、主动回忆和研究问题取舍。
- Codex 可推进通常包括刷新状态、精读下一篇、补知识卡、补图谱关系和更新项目综述。
- 协作层不替代项目看板；它是跨项目的执行分工页。

## 自动归档策略契约

`vault/13_Knowledge_Graph/archive_policy.json` 是归档策略状态；`archive_policy.html` 是用户侧默认入口。

归档策略应满足：

- 明确 canonical source、generated assets、backup zips、logs、raw files 和 cache files 的处理边界。
- 默认只报告和生成策略，不删除不确定研究文件。
- zip 备份裁剪必须通过显式命令执行，例如 `make workflow-backup-prune KEEP=30`。
- `.DS_Store` 和 `__pycache__` 属于可安全清理缓存，但仍以报告为主。
- 日志压缩优先生成 compact summary，原始 daily log 默认保留。

## Schema 校验契约

`make schema-validate` 校验这些机器可读状态文件：

- `vault/13_Knowledge_Graph/artifact_manifest.csv`
- `vault/13_Knowledge_Graph/search_index.json`
- `vault/14_Review_Queue/review_state.json`
- `vault/13_Knowledge_Graph/workflow_state.json`
- `vault/13_Knowledge_Graph/action_queue.json`
- `vault/13_Knowledge_Graph/workflow_audit_report.json`
- `vault/13_Knowledge_Graph/collaboration_state.json`
- `vault/13_Knowledge_Graph/archive_policy.json`
- `projects/*/project_state.json`

校验重点：

- 必需字段存在，顶层类型正确。
- 计数字段与实际数组长度一致。
- 用户侧入口必须指向存在的 HTML 页面。
- 项目状态中的 `entrypoints` 是展示入口；原始 Markdown 路径应放在 source 或 project metadata 中。
- 审计报告 JSON 的 `summary.counts` 必须与 `checks` 数组一致。

## 审计报告数据契约

`vault/07_Codex_Logs/workflow_audits/YYYY-MM-DD-workflow-audit.md` 是按日期归档的人类日志；`workflow_health.html` 是用户侧体检页；`vault/13_Knowledge_Graph/workflow_audit_report.json` 是自动化默认读取的最新审计数据。

以后需要读取最近审计结果时，应优先读 `workflow_audit_report.json`，不要解析 Markdown 审计日志。

## 改造优先级

1. 先保证链接路由和 artifact manifest 稳定。
2. 再拆分大型生成脚本，减少单文件职责。
3. 再结构化项目状态，供每日推荐和综述更新使用。
4. 先用 manifest 派生的轻量搜索页解决发现问题。
5. 只有当本地 JSON 搜索明显不够用时，再考虑交互式浏览器应用或数据库。

## 验收标准

一次合格的刷新应满足：

- 打开 `study_dashboard.html` 后可以进入所有核心功能。
- 用户侧 HTML 页面没有本地 `.md` 直链。
- 新增论文、知识卡、日志和目录入口都出现在 artifact manifest。
- `search/index.html` 和 `search_index.json` 已刷新，搜索结果只打开 HTML 展示页。
- 知识图谱 CSV 与 HTML 图谱都能刷新。
- 复习队列包含新增知识点或明确标注无需复习，且 `review_state.json`、`knowledge_cards/review_today.html` 已刷新。
- `workflow-audit` 没有 FAIL；如有 WARN，必须说明证据边界或待处理事项。
- `project_collaboration.html` 与 `archive_policy.html` 已刷新，且对应 JSON 通过 schema 校验。

## 审计覆盖范围

`make workflow-audit` 不只检查入口是否存在，还应检查这些契约是否仍然成立：

- 用户侧 HTML 页面没有裸 Markdown 直链，且本地链接可解析。
- Markdown 镜像页未落后于源文件。
- `artifact_manifest.csv` 字段完整、展示页存在、核心展示类型齐全。
- `search_index.json` 条目计数正确，所有搜索结果都指向存在的 HTML 页面。
- `review_state.json` 与 `review_queue.csv` 的总数和到期数一致，重点复习项有 HTML 展示页。
- `projects/*/project_state.json` 存在，并包含今日精读、今日复习、搜索、manifest 和 search index 等关键入口。
- `workflow_state.json` 与 `workflow_state.html` 已刷新，能聚合当前项目、复习、搜索、图谱和审计状态。
- `action_queue.json` 与 `action_queue.html` 已刷新，所有行动入口都指向存在的 HTML 页面。
- `collaboration_state.json` 与 `project_collaboration.html` 已刷新，所有项目入口指向存在的 HTML 页面。
- `archive_policy.json` 与 `archive_policy.html` 已刷新，能报告备份、日志、生成资产和缓存策略。
- `workflow_audit_report.json` 已刷新，且 schema 校验通过。
- 图谱 CSV 和图谱 HTML 均可用。
