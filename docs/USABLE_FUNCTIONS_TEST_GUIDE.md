# 可用功能测试与使用手册

Last updated: 2026-07-02

这份手册只列当前已经能用的功能，并说明它们有什么用、什么时候用、怎么用、怎么测试。默认工作目录：

```bash
cd /Users/leung/ResearchWorkflow
```

如果你不是在测试命令，而是想正常使用，请优先打开用户首页：

```bash
make home
```

或直接对 Codex 说：

```text
打开科研首页，告诉我今天应该怎么继续。
```

当前图书馆短视频项目的阅读入口：

```bash
make reading-board PROJECT=library_short_video
```

已读论文的省 token 带读入口：

```bash
make paper-context PROJECT=library_short_video ALL=1
make typora-project PROJECT=library_short_video DOC=contextpacks
```

测试时优先使用示例项目：

```bash
PROJECT=starter_project
```

真实研究时把 `starter_project` 换成你的项目 slug，例如 `PROJECT=cnki_ai_knowledge_service`。

## 0. 使用原则

- 你可以直接用自然语言让我做事，不必记命令。命令主要用于你想逐一测试时。
- 真实 CNKI 文献和 PDF 必须来自你的合法访问路径。不要把账号密码发给 Codex；验证码、机构确认、付费墙由你在浏览器里处理。
- 文献摘要、AI 总结、metadata-only 不能直接当作论文证据。真正支撑正文论断的文献需要 `human-read` 或 `verified`，并有 PDF、reader 或笔记定位。
- 先用 `starter_project` 做 smoke test；等流程熟悉后，再用真实项目和真实 CNKI 导出文件测试。

## 1. 最推荐的逐项测试路线

### 1.0 工作流回归测试

用途：快速检查核心 HTML 入口、链接、推荐队列、复习按钮、知识图谱视图、证据核验表和写作面板是否还能正常使用。

```bash
make workflow-test
```

这条命令只读当前产物，不刷新页面、不改 CSV、不提交 Git。每次运行 `make learning-dashboard`、`make incoming-triage` 或改展示层脚本后，建议先跑它，再跑 schema 和 audit。

### 1.0.1 审计与渲染分层

用途：把“刷新状态页”和“检查当前状态”分开。

```bash
make workflow-render
make workflow-audit-readonly
make workflow-audit
```

- `workflow-render`：刷新总状态、行动队列、协作层和归档策略，有副作用。
- `workflow-audit-readonly`：只读检查当前产物，只写审计报告和体检页。
- `workflow-audit`：日常组合命令，先 render，再 readonly audit。

### 1.0.2 文献状态机

用途：通过正式状态流转更新 `library/literature_matrix.csv` 的 `read_status`，并写入事件日志。

```bash
make lit-transition CITEKEY=cnki_2024_xxx FROM=metadata-only TO=fulltext-available REASON="Authorized PDF added"
make lit-transition CITEKEY=cnki_2024_xxx FROM=skimmed TO=human-read REASON="Finished close reading" EVIDENCE="Reader notes checked"
```

状态规则见 `docs/STATE_MACHINE.md`。

### 1.1 基础环境

用途：确认 Python、R、Pandoc、Gephi、Typora、PDF 解析包是否可用。

```bash
make check
```

你应该关注：

- `Python`、`R`、`Pandoc`、`Gephi`、`Typora` 是否 OK。
- `fitz`、`pdfplumber`、`pypdf` 是否 OK。
- 当前已知缺口：`MATLAB` 和 `Tectonic` 命令行入口未接入。

### 1.2 项目状态

用途：快速知道一个项目现在缺什么、下一步该做什么。

```bash
make status PROJECT=starter_project
```

实用说法：

```text
帮我检查 starter_project 现在做到哪一步，并给出下一步建议。
```

### 1.3 Typora 打开项目文档

用途：用 Typora 阅读或人工改 Markdown。

```bash
make typora-project PROJECT=starter_project DOC=dashboard
make typora-project PROJECT=starter_project DOC=paper
make typora FILE=README.md
```

常用 `DOC`：

- `dashboard`: 项目看板
- `rq`: 研究问题
- `literature`: 文献综述
- `experiment`: 实验计划
- `results`: 结果解释
- `claims`: 主张-证据映射
- `readiness`: 投稿准备度
- `paper`: 论文主稿
- `terms`: 术语表
- `polishing`: 润色记录
- `response`: 审稿回复 tracker

## 2. Codex 会话、日志和上下文管理

### 2.1 会话启动

用途：每次继续科研时读取 hot context、open loops、user model 和 context index。

```bash
make codex-start
```

实用说法：

```text
继续上次科研工作，先读取当前上下文和开放问题。
```

### 2.2 Fast-lane 快速状态

用途：处理小任务时减少 token 和文件联动。它只生成一个运行快照，不强制改项目看板、daily log、file sweep 或 compact summary。

```bash
make fast-status PROJECT=library_short_video TOPIC="图书馆短视频相关研究" PRINT=1
make workflow-policy
```

输出位置：

```text
codex/runtime/<project>_fast_snapshot.md
codex/runtime/quick_events.jsonl
```

适合这些说法：

```text
用快速模式告诉我下一篇该读什么。
快速看一下这个项目现在做到哪一步。
只查 reader/context pack 路径，不做完整归档。
```

完整说明：

```text
docs/WORKFLOW_ARCHITECTURE_FASTLANE.md
```

### 2.3 文件活动扫描

用途：记录当天新增或修改了哪些文件，方便以后追溯。

```bash
make codex-sweep
```

输出位置：

```text
vault/07_Codex_Logs/file_sweeps/
```

### 2.4 每日日志压缩

用途：把长日志压缩成摘要，降低后续上下文读取成本。

```bash
make codex-compact
make codex-compact DATE=2026-06-20
```

输出位置：

```text
vault/07_Codex_Logs/compact_daily/
```

### 2.5 全量日志压缩和索引

用途：日志很多后批量压缩，并更新 context index。

```bash
make codex-compact-all
make codex-context-index
make codex-context-audit
```

实用方法：长时间使用后，不默认读原始 daily log；优先读 `current_context.md`、`open_loops.md`、`user_model.md`、`context_index.md` 和 compact summary。

### 2.6 每周总结

用途：把一周科研工作、决策、文件、问题和下周重点汇总。

```bash
make codex-weekly
```

输出位置：

```text
vault/08_Weekly_Reviews/
```

实用说法：

```text
帮我做本周科研复盘，总结进展、问题和下周优先级。
```

## 3. 项目管理

### 3.1 新建项目

用途：为一个论文、实验或选题创建标准目录。

```bash
make new SLUG=my_project TITLE="我的研究题目"
```

会生成：

- 研究问题、方法、文献综述、实验计划、假设登记、结果解释、claim-evidence map
- `manuscript/` 中文论文主稿、术语表、润色记录、投稿检查清单
- `data/` 数据字典、codebook、数据治理
- `figures/` 原始图、最终图、图件合同
- `presentations/` 论文汇报/PPT 计划
- `review_response/` 审稿回复 tracker
- `passport/` 材料完整性清单

实用说法：

```text
为“生成式 AI 对图书馆知识服务的影响”创建一个新研究项目，并先写研究问题草稿。
```

### 3.2 项目状态看板

用途：检查项目缺失材料和建议下一步。

```bash
make status PROJECT=my_project
```

### 3.3 旧项目补齐新模板

用途：旧项目缺少后来新增的模板时补齐，默认不覆盖已有文件。

```bash
make backfill PROJECT=my_project
make backfill PROJECT=my_project APPLY=1
make backfill-all
make backfill-all APPLY=1
```

使用方法：先不带 `APPLY=1` 看会补哪些文件；确认后再加 `APPLY=1`。

### 3.4 Material Passport

用途：给项目关键文件生成 hash 和审计清单，适合投稿、组会、阶段归档前使用。

```bash
make passport PROJECT=my_project
```

输出位置：

```text
projects/my_project/passport/
```

## 4. 中文研究与《图书情报工作》适配

### 4.1 目标期刊 profile

用途：把项目默认放到中文图情研究和《图书情报工作》语境里，检查选题、摘要、长英文摘要、GB/T 7714、数据共享和 AI 披露。

关键文件：

```text
docs/journal_profiles/tushuqingbaogongzuo.md
projects/<slug>/manuscript/target_journal.md
projects/<slug>/manuscript/submission_checklist_tushuqingbaogongzuo.md
```

实用说法：

```text
按《图书情报工作》的目标期刊要求，检查这个项目的论文结构和投稿风险。
```

### 4.2 中文论文写作骨架

用途：围绕中文学术论文写作组织标题、摘要、关键词、引言、方法、结果、讨论、结论。

关键文件：

```text
projects/<slug>/manuscript/paper.md
```

打开测试：

```bash
make typora-project PROJECT=starter_project DOC=paper
```

### 4.3 术语表

用途：正式写作或润色前统一核心概念、模型名、数据集、指标、缩写和单位。

关键文件：

```text
projects/<slug>/manuscript/terminology_ledger.md
```

打开测试：

```bash
make typora-project PROJECT=starter_project DOC=terms
```

实用说法：

```text
帮我整理这篇中文论文的术语表，统一核心概念、缩写和英文译名。
```

### 4.4 润色记录

用途：保留重要改写、术语变更、论证结构调整和 AI 辅助痕迹。

关键文件：

```text
projects/<slug>/manuscript/polishing_log.md
```

打开测试：

```bash
make typora-project PROJECT=starter_project DOC=polishing
```

实用说法：

```text
润色这段中文论文文字，同时把关键修改记录进 polishing log。
```

### 4.5 AI 使用披露

用途：投稿前说明 AI 在检索、总结、写作、润色、代码或图表中的辅助角色。

关键文件：

```text
projects/<slug>/manuscript/ai_usage_disclosure.md
```

实用说法：

```text
根据我们实际使用 AI 的情况，帮我写一版投稿用 AI 使用披露。
```

### 4.6 数据治理与数据可用性

用途：管理数据来源、字段解释、敏感信息、清洗流程和可共享边界。

关键文件：

```text
projects/<slug>/data/data_dictionary.md
projects/<slug>/data/codebook.md
projects/<slug>/data/data_governance.md
```

实用说法：

```text
根据这个数据文件，帮我建立数据字典、codebook 和数据可用性说明。
```

## 5. 文献检索、CNKI 和阅读

### 5.1 OpenAlex 文献检索

用途：获取开放论文元数据，适合国际文献或快速补充背景。

```bash
make search Q="generative AI knowledge service"
```

输出位置：

```text
library/search_results/
library/references.bib
```

注意：需要网络访问。

### 5.2 检索结果导入文献矩阵

用途：把检索结果纳入长期文献库。

```bash
make import-matrix CSV=library/search_results/<file>.csv
```

核心输出：

```text
library/literature_matrix.csv
```

### 5.3 CNKI 导出文件导入

用途：把 CNKI 导出的 CSV、TSV、XLSX、RIS、EndNote 文本导入文献矩阵。

先 dry-run：

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=my_project DRY=1
```

确认后导入：

```bash
make import-cnki INPUT=library/cnki_exports/<file> TAG=my_project
```

输出：

```text
library/literature_matrix.csv
library/cnki_exports/import_reports/
```

实用方法：

1. 你在浏览器里用机构/VPN/图书馆入口打开 CNKI。
2. 我帮你设计中文检索式、筛选条件和字段要求。
3. 你导出检索结果放到 `library/cnki_exports/`。
4. 我导入、去重、打标签、生成报告。

### 5.4 CNKI 前沿雷达

用途：从已导入的 CNKI 元数据中筛 5-7 篇近期候选文献，生成摘要级学习 digest 和讨论问题。

```bash
make cnki-frontier TAG=my_project TOPIC="生成式人工智能与知识服务"
```

可选参数：

```bash
make cnki-frontier TAG=my_project TOPIC="生成式人工智能与知识服务" LIMIT=7 SINCE=2022
make cnki-frontier TAG=my_project KEYWORDS="图书馆,知识服务,生成式人工智能"
```

输出位置：

```text
vault/15_CNKI_Frontier/digests/
```

实用说法：

```text
基于我已导入的 CNKI 文献，生成今天的 5-7 篇前沿阅读清单，并给我讨论问题。
```

### 5.5 单篇研讨卡

用途：先判断一篇论文是否值得全文精读，生成摘要、方法线索、可能创新点、差异点和升级精读路径。

```bash
make paper-brief CITEKEY=<citekey>
make paper-brief TITLE="论文标题"
```

输出位置：

```text
vault/15_CNKI_Frontier/paper_briefs/
```

### 5.6 全文 reader

用途：对合法获取的 PDF 或文本生成 source-grounded reader 包，包含 `paper.md`、`source_map.json`、`translation_notes.md` 和 assets 文件夹。

```bash
make paper-reader PROJECT=my_project CITEKEY=<citekey> PDF=library/pdfs/<paper>.pdf
make paper-reader PROJECT=my_project TITLE="论文标题" TEXT=library/text/<paper>.txt
```

输出位置：

```text
projects/my_project/literature/readers/<citekey>/
```

重要限制：这个命令不会自动把文献标记为 `human-read`。只有你实际读完并确认后，才应更新阅读状态。

实用说法：

```text
用这篇合法获取的 PDF 生成全文 reader，保留 source map，方便我逐段精读。
```

### 5.7 OA PDF 下载

用途：下载开放获取 PDF。

```bash
make download
```

注意：只处理开放获取或合法可下载的 PDF，不绕过付费墙。

### 5.8 PDF 文本提取

用途：把 PDF 转成可读文本，供摘要、阅读、审计使用。

```bash
make extract
```

当前可用后端：

- `fitz` / PyMuPDF
- `pdfplumber`
- `pypdf`

### 5.9 Obsidian 文献卡片

用途：从检索 CSV 的某一行生成 Obsidian 文献笔记。

```bash
/Users/leung/anaconda3/bin/python scripts/add_literature_note.py --csv library/search_results/<file>.csv --citekey <citekey>
```

输出位置：

```text
vault/01_Literature/
```

实用说法：

```text
给这篇论文建立 Obsidian 文献卡片，并链接到当前项目。
```

## 6. 证据、引用和投稿包

### 6.1 证据门禁

用途：检查 metadata-only、abstract-only、AI-summarized、unread 或没有 source locator 的材料是否被误用为正文证据。

```bash
make evidence-gate PROJECT=my_project
make evidence-gate PROJECT=my_project STRICT=1
```

输出：

```text
projects/my_project/manuscript/evidence_gate_report.md
```

实用方法：写论文前、投稿前、claim-evidence map 更新后都跑一次。

### 6.2 GB/T 7714 引用审计

用途：检查正文引用、参考文献、中文参考文献英译、文献类型标识、DOI/URL 和证据门禁问题。

```bash
make citation-audit PROJECT=my_project
make citation-audit PROJECT=my_project STRICT=1
```

输出：

```text
projects/my_project/manuscript/citation_audit_gbt7714.md
```

实用说法：

```text
帮我检查这篇论文的 GB/T 7714、正文引用和中文参考文献英译问题。
```

### 6.3 《图书情报工作》投稿包

用途：生成投稿前本地材料包，包括主文稿、DOCX、引用审计、证据门禁、数据可用性、AI 披露、图件、完整性材料、投稿信草稿、manifest 和 checksum。

```bash
make submission-package PROJECT=my_project
make submission-package PROJECT=my_project NO_DOCX=1
make submission-package PROJECT=my_project STRICT=1
make submission-package PROJECT=my_project STRICT=1 NO_DOCX=1
```

输出位置：

```text
projects/my_project/submission_package/
```

注意：投稿包会刻意排除 raw data，避免把不该提交的原始数据打包进去。

## 7. 想法孵化、选题和快乐科研闭环

### 7.1 Idea Lab 头脑风暴

用途：把灵感、困惑、前沿信号转成 idea cards，再用 FINER 初筛，成熟后推进为项目。

```bash
make idea-start TOPIC="生成式人工智能与图书馆知识服务"
make idea-status
```

输出位置：

```text
vault/11_Idea_Lab/
```

实用说法：

```text
帮我开一个头脑风暴会话，结合已有积累和领域前沿，引导我产生新的科研想法。
```

### 7.2 假设登记

用途：把“我猜”“我觉得”“我想验证”转成可检验 hypothesis。

关键文件：

```text
projects/<slug>/05_hypothesis_registry.md
```

实用说法：

```text
把这个猜想登记成 hypothesis，并说明需要什么数据和方法验证。
```

### 7.3 实验计划

用途：把问题转成数据、方法、指标、步骤和可复现执行方案。

关键文件：

```text
projects/<slug>/04_experiment_plan.md
```

实用说法：

```text
根据这个研究问题，帮我设计一个可执行的实验计划。
```

### 7.4 结果解释

用途：判断结果支持、反驳还是无法判断你的假设，并把结果转成可写进论文的解释。

关键文件：

```text
projects/<slug>/06_result_interpretation.md
```

实用说法：

```text
解释这个实验结果，判断它支持还是反驳我的猜想，并提醒可能的替代解释。
```

### 7.5 主张-证据映射

用途：把文献、数据、图表和论文论断对齐，避免写作时证据不足。

关键文件：

```text
projects/<slug>/07_claim_evidence_map.md
```

打开测试：

```bash
make typora-project PROJECT=starter_project DOC=claims
```

实用说法：

```text
把这些结果转成 claim-evidence map，标出哪些论断证据还不够。
```

## 8. 实验、复现和数据分析

### 8.1 Python/R 实验脚本

用途：项目模板已经有 Python、R、MATLAB 脚本位置。

关键位置：

```text
projects/<slug>/analysis/python/analysis.py
projects/<slug>/analysis/R/analysis.R
projects/<slug>/analysis/matlab/simulation.m
```

注意：Python 和 R 当前可用；MATLAB 脚本目录存在，但 MATLAB 命令行入口未检测到。

### 8.2 记录一次实验运行

用途：运行命令并记录日志、返回码、环境和输出路径。

```bash
/Users/leung/anaconda3/bin/python scripts/run_experiment.py --project starter_project --name smoke_python -- /Users/leung/anaconda3/bin/python projects/starter_project/analysis/python/analysis.py
```

实用说法：

```text
运行这个 Python/R 实验，并把命令、输出和环境记录到项目里。
```

### 8.3 CSV 复现比较

用途：比较两次 CSV 输出是否一致，适合复现实验和回归检查。

```bash
make compare-results EXPECTED=path/to/expected.csv ACTUAL=path/to/actual.csv OUTPUT=path/to/report.md
```

实用说法：

```text
比较这两次实验结果是否一致，生成复现报告。
```

## 9. 图表、Gephi 和可视化

### 9.1 Gephi 网络数据导出

用途：把节点和边导出成 Gephi 可读格式，用于知识图谱、共现网络、引用网络等。

```bash
make gephi
```

输出位置通常在：

```text
library/gephi/
```

实用说法：

```text
把这些文献/概念关系导出成 Gephi 网络图数据。
```

### 9.2 Obsidian 知识图谱导出

用途：把 Obsidian 双链笔记导出成 nodes/edges，便于 Gephi 可视化。

```bash
make obsidian-graph
```

输出位置：

```text
vault/13_Knowledge_Graph/
```

### 9.3 论文图件合同

用途：正式画图前定义每张图的结论、数据来源、统计方法、面板结构、导出格式和审稿风险。

关键文件：

```text
projects/<slug>/figures/specs/figure_spec.md
```

实用说法：

```text
帮我为这张论文图写 figure spec，明确它要证明什么、需要哪些数据和导出格式。
```

### 9.4 nature-figure 作图 skill

用途：生成或修改投稿级科研图、多面板图、统计图，支持 Python 或 R。

使用前必须选择后端：

```text
用 Python 帮我画一张论文图，数据在 xxx.csv，目标是说明 xxx。
```

或：

```text
用 R 帮我画一张论文图，适合投稿《图书情报工作》，需要可编辑 PDF/SVG。
```

实用方法：先写 `figure_spec.md`，再画图；导出结果放 `figures/final/`，原始草图放 `figures/raw/`。

## 10. 写作、润色、PPT 和审稿回复

### 10.1 nature-polishing 润色

用途：中文论文改写、英文润色、摘要/引言/讨论优化、术语统一、LaTeX 排版问题诊断。

实用说法：

```text
请按中文核心期刊风格润色这段文字，保持学术严谨，不要夸大结论。
```

```text
把这段中文摘要改成更适合《图书情报工作》的结构化摘要。
```

建议配合：

```text
projects/<slug>/manuscript/terminology_ledger.md
projects/<slug>/manuscript/polishing_log.md
```

### 10.2 nature-reader 精读

用途：读论文、翻译论文、做中英文对照、保留图表和 source anchors。

实用说法：

```text
帮我精读这篇 PDF，生成中英文对照 reader，保留图表位置和 source map。
```

如果只需要摘要级研讨，先用：

```bash
make paper-brief CITEKEY=<citekey>
```

如果要全文 grounded reader，用：

```bash
make paper-reader PROJECT=<slug> CITEKEY=<citekey> PDF=<path>
```

### 10.3 nature-paper2ppt

用途：把论文、PDF、阅读笔记或摘要做成中文组会 PPT、文献汇报、读书报告。

实用说法：

```text
把这篇论文做成 15 分钟组会 PPT，中文讲稿，重点讲研究问题、方法、结果、创新和不足。
```

建议配合：

```text
projects/<slug>/presentations/paper2ppt_plan.md
```

### 10.4 nature-response

用途：审稿意见回复、逐点回复、返修信、rebuttal。

实用说法：

```text
根据这些审稿意见，帮我写逐点回复，区分已经修改、计划补充和需要礼貌解释的部分。
```

建议配合：

```text
projects/<slug>/review_response/response_tracker.md
```

### 10.5 academic-research-suite

用途：研究计划、文献综述、论文大纲、摘要、引用检查、审稿人模拟、完整研究到论文流程。

实用说法：

```text
用 ARS 帮我为这个选题做研究计划和论文结构。
```

```text
用 ARS reviewer 视角审查这篇论文草稿，重点找逻辑漏洞、证据不足和方法风险。
```

### 10.6 jupyter-notebook

用途：创建、整理或编辑 `.ipynb` 实验笔记。

实用说法：

```text
帮我为这个数据分析任务创建一个 Jupyter notebook，包含数据读取、清洗、分析和图表输出。
```

### 10.7 pdf skill

用途：PDF 读取、创建、合并、提取、视觉版面检查。

实用说法：

```text
帮我检查这个 PDF 的页面版式、图表是否清晰、文字是否溢出。
```

## 11. 知识导师和 Obsidian

### 11.1 Knowledge Coach 状态

用途：查看概念卡片、方法卡片、复习队列的基本状态。

```bash
make knowledge-status
```

### 11.2 概念/方法解释并建卡

用途：遇到不懂的理论、方法、统计概念时，先通俗解释，再做 Obsidian 卡片并加入复习。

实用说法：

```text
用通俗例子教我扎根理论，并结合图书情报研究举一个例子，最后做成 Obsidian 方法卡片。
```

输出位置：

```text
vault/02_Concepts/
vault/03_Methods/
vault/12_Learning_Log/
vault/14_Review_Queue/
```

## 12. 当前可用但需要真实输入才能完整测试的功能

### 12.1 CNKI 页面协作

能做：

- 帮你设计检索式。
- 在你授权的本地浏览器会话中辅助操作页面。
- 优先从检索结果点击论文题名进入详情页，再点击 `PDF下载` 获取 PDF。
- 导入 CNKI 导出文件。
- 整理 PDF、生成 reader、前沿雷达和研讨卡。

不能做：

- 不接收 CNKI 密码。
- 不绕过验证码、付费墙、下载限制或机构访问控制。
- 详情页没有 PDF 权限或按钮时，只能使用合法可得的结果页下载、CAJ 转换或人工导出路线。
- 不把 metadata-only 摘要当作已读证据。

### 12.2 真实投稿包

能测试命令：

```bash
make submission-package PROJECT=starter_project NO_DOCX=1
```

真正有价值的测试需要：

- 一个真实项目。
- 初步论文主稿。
- 参考文献。
- 图件或图件 specs。
- 数据可用性和 AI 披露。

### 12.3 真实数据治理

当前已有模板，但需要真实数据校准：

- 字段命名
- 缺失值
- 敏感信息
- 数据共享边界
- 处理脚本和可复现记录

## 13. 当前明确未完全接入的功能

### 13.1 MATLAB

状态：项目目录和模板存在，但 `make check` 未检测到 MATLAB 命令行入口。

可先做：

```text
帮我审查 MATLAB 脚本逻辑，或规划 MATLAB 实验。
```

暂不能稳定做：

```text
直接从命令行运行 MATLAB 仿真。
```

### 13.2 Tectonic / LaTeX PDF 编译

状态：Pandoc 可用，Tectonic 未检测到。

可用：

```bash
make submission-package PROJECT=<slug>
```

暂不能保证：

```text
用 Tectonic 从 LaTeX 稳定编译正式 PDF。
```

## 14. 最实用的日常用法模板

### 14.1 今天不知道做什么

```text
继续上次科研工作，先帮我看当前进度、开放问题和今天最值得推进的三件事。
```

### 14.2 找中文文献

```text
请围绕“生成式人工智能与图书馆知识服务”设计 CNKI 检索式、筛选条件和导出字段。
```

### 14.3 每日读 5-7 篇前沿文献

```text
基于我导入的 CNKI 文献，生成今天的前沿雷达，筛 5-7 篇，按主题聚类并给出研讨问题。
```

### 14.4 精读其中一篇

```text
我想详细看这篇论文。请先做单篇研讨卡；如果值得读，再用 PDF 生成全文 reader，总结摘要、方法、创新点、不同之处和可借鉴点。
```

### 14.5 写中文论文

```text
按《图书情报工作》的风格，帮我把这个研究问题扩展成论文大纲，并检查每个部分需要什么证据。
```

### 14.6 润色中文段落

```text
润色下面这段中文论文文字，要求更清晰、克制、符合图情期刊风格，并指出哪些表述证据不足。
```

### 14.7 画论文图

```text
用 Python 画一张投稿级论文图。先帮我写 figure spec，再根据数据生成图，输出 SVG/PDF/PNG。
```

### 14.8 投稿前检查

```text
请按《图书情报工作》投稿前标准，依次检查证据门禁、GB/T 7714、AI 披露、数据可用性、图件和投稿包。
```

## 15. 推荐测试记录方式

每测试一个功能，建议记录：

```text
功能：
测试命令或说法：
输入文件：
输出文件：
是否成功：
发现的问题：
下一步修正：
```

你也可以直接说：

```text
我们开始逐一测试功能。每测完一个，请你记录结果、问题和下一步。
```
