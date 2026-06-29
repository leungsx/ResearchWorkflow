# ResearchWorkflow

这是一个面向科研全过程的本地工作流骨架，目标是把文献检索、PDF 管理、文献摘要、实验计算、绘图、论文写作、排版、完整性检查和 Obsidian 知识库连接起来。

## 快速开始

```bash
cd /Users/leung/ResearchWorkflow
make check
make workflow-audit
make workflow-refresh-git DATE=2026-06-29 NOTE="daily closeout"
make new SLUG=my_first_paper TITLE="My First Paper"
make status PROJECT=my_first_paper
make evidence-gate PROJECT=my_first_paper
make citation-audit PROJECT=my_first_paper
make submission-package PROJECT=my_first_paper
```

把 `/Users/leung/ResearchWorkflow/vault` 作为 Obsidian vault 打开即可开始做知识库。

使用者可视化指南见 `docs/USER_VISUAL_GUIDE.md`。如果只想知道“我该怎么用、哪些功能已实现、哪些还在规划”，先看这份文档。

逐项测试和实操说明见 `docs/USABLE_FUNCTIONS_TEST_GUIDE.md`，其中按功能列出用途、输入、输出、测试命令、自然语言说法和注意事项。

## 目录结构

- `library/`: 全局文献库，放检索结果、PDF、BibTeX、提取文本和 Gephi 数据。
- `projects/`: 每个论文或实验项目一个独立目录。
- `vault/`: Obsidian 知识库，用来记录论文卡片、概念卡片、方法卡片和项目日志。
- `scripts/`: 自动化脚本，用于检索文献、下载开放 PDF、提取文本、生成笔记、记录实验和导出 Gephi 数据。
- `templates/` 和 `vault/99_Templates/`: 可复用模板。
- `docs/`: 工作流规范、安装说明和科研完整性检查规则。
- `prompts/`: 之后让 Codex/AI 按固定格式帮你做文献综述、实验验证和论文写作的提示词。
- `vault/11_Idea_Lab/`: 头脑风暴、科研想法、前沿扫描和 idea cards。
- `vault/12_Learning_Log/`: 学习记录和知识点解释。
- `vault/13_Knowledge_Graph/`: Obsidian 知识图谱导出。
- `vault/14_Review_Queue/`: 知识点和方法复习队列。

可用性改进路线图见 `docs/USABILITY_REVIEW.md`。

Codex-first 协作协议见 `codex/OPERATING_PROTOCOL.md`。科研会话默认由 Codex 维护每日日志、周总结、上下文包和用户模型。

Git/GitHub 备份策略见 `docs/GIT_BACKUP_STRATEGY.md`。原则是 Git 只管理文本、结构、脚本、仪表盘和可回溯记录；PDF、CAJ、zip 备份、缓存和大型二进制文件不进入 Git。

科研想法孵化与头脑风暴见 `docs/IDEA_LAB.md`。

从灵感、假设、实验、结果到论文主张的轻量闭环见 `docs/HAPPY_RESEARCH_LOOP.md` 和 `docs/EXPERIMENT_TO_CLAIM.md`。

从使用者角度评审“快乐科研”体验的改进建议见 `docs/UX_REVIEW_HAPPY_RESEARCH.md`。

科研知识导师、方法训练、复习和知识图谱见 `docs/KNOWLEDGE_COACH.md` 与 `docs/OBSIDIAN_KNOWLEDGE_GRAPH.md`。

借鉴 `nature-*` skills 后新增的投稿/汇报生产层见 `docs/NATURE_SKILL_INTEGRATION.md`，覆盖精读 source map、术语表、润色记录、图件合同、PPT 资产清单和审稿回复 tracker。

默认中文目标期刊 profile 见 `docs/journal_profiles/tushuqingbaogongzuo.md`，当前已按《图书情报工作》的选题范围、中文结构化摘要、长英文摘要、GB/T 7714、数据共享和 AI 披露要求优化项目模板。

CNKI/知网文献流程见 `docs/CNKI_WORKFLOW.md`。你通过自己的机构账号、VPN 或图书馆入口合法访问 CNKI，Codex 负责检索策略、导出结果导入、文献矩阵、PDF 组织和阅读记录；不接收账号密码，也不绕过验证码、付费墙或下载限制。每日/每次会话的前沿阅读机制见 `docs/CNKI_FRONTIER_RADAR.md`。

旧项目可用 `make backfill PROJECT=<slug> APPLY=1` 补齐后来新增的模板文件；默认不覆盖已有文件。投稿前先用 `make evidence-gate PROJECT=<slug>` 检查证据阅读状态和 source locator，再用 `make citation-audit PROJECT=<slug>` 生成 GB/T 7714、中文参考文献英译和证据门禁合并报告，最后用 `make submission-package PROJECT=<slug>` 生成投稿包。

本机已接入 Typora 作为 Markdown 阅读/人工编辑入口。Codex 继续负责生成、归档和维护文件；需要预览时可用 `make typora FILE=<path>` 或 `make typora-project PROJECT=<slug> DOC=paper` 打开。

## 推荐工作流

0. **每日入口**: 直接打开 `paper_reading/today.html` 阅读当天精读页；需要全局总览时打开 `study_dashboard.html`。
0.1. **工作流体检**: 运行 `make workflow-audit`，查看 `workflow_health.html`，确认入口、图谱、镜像页、归档和备份状态。
0.2. **日终维护**: 用户侧页面、证据状态或图谱变化后，运行 `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE="<说明>"`，顺序刷新图谱、仪表盘、备份、文件归类、压缩摘要、体检报告，并把可追踪文本资产提交/推送到私有 Git 远程。只做本地刷新时用 `make workflow-refresh`。
1. **知识补课**: 遇到不懂的概念或科研方法时，Codex 负责解释、举例、建卡、复习和入图谱。
2. **想法孵化**: 用 Idea Lab 记录头脑风暴、前沿信号和 idea cards。
3. **研究问题**: 在 `projects/<slug>/01_research_question.md` 收敛 RQ、变量、范围和预期贡献。
4. **假设登记**: 在 `05_hypothesis_registry.md` 保存可检验猜想。
5. **文献检索**: 用 `scripts/literature_search.py` 从 OpenAlex 检索开放元数据。
6. **文献入库**: 用 `make import-matrix CSV=<search_csv>` 把 OpenAlex 检索结果导入 `library/literature_matrix.csv`；知网导出结果用 `make import-cnki INPUT=<file> TAG=<slug>` 导入。
7. **CNKI 前沿雷达**: 导入知网导出结果后，用 `make cnki-frontier TAG=<slug>` 生成 5-7 篇前沿候选，选 1 篇进入研讨。
8. **单篇研讨卡与全文 reader**: 用 `make paper-brief CITEKEY=<citekey>` 生成摘要级研讨卡；有合法全文后用 `make paper-reader PROJECT=<slug> CITEKEY=<citekey> PDF=<path>` 生成 source-grounded reader。
9. **PDF 与笔记**: 用 `download_oa_pdfs.py` 下载开放获取 PDF，用 `extract_pdf_text.py` 提取文本，用 `add_literature_note.py` 生成 Obsidian 文献卡片。
10. **文献矩阵**: 在 `library/literature_matrix.csv` 维护理论、方法、数据、结论、局限和可引用证据。
11. **实验与仿真**: 在项目目录的 `analysis/python`、`analysis/R`、`analysis/matlab` 放分析脚本，用 `run_experiment.py` 记录每次运行。
12. **结果解释**: 在 `06_result_interpretation.md` 判断结果支持、反驳还是无法判断猜想。
13. **主张证据映射**: 在 `07_claim_evidence_map.md` 把实验结果、文献和论文主张对齐。
14. **目标期刊适配**: 在 `manuscript/target_journal.md` 判断文章类型、选题契合、图情领域贡献和《图书情报工作》投稿约束。
15. **术语锁定**: 在 `manuscript/terminology_ledger.md` 统一方法、模型、数据集、指标、缩写和单位，再开始正式润色。
16. **绘图**: 原始图放 `figures/raw`，可发表图放 `figures/final`，每张图必须有 `figures/specs` 中的图件合同。Gephi 网络图流程见 `docs/GEPHI_WORKFLOW.md`。
17. **写作与润色**: 在 `manuscript/paper.md` 写中文主稿，引用写进 `manuscript/references.bib`，重要润色记录写入 `manuscript/polishing_log.md`。
18. **投稿检查**: 用 `manuscript/submission_checklist_tushuqingbaogongzuo.md` 检查摘要、长英文摘要、GB/T 7714、数据可用性、AI 披露和作者贡献。
19. **证据与引用审计**: 运行 `make evidence-gate PROJECT=<slug>`，再运行 `make citation-audit PROJECT=<slug>`，生成证据门禁和 `manuscript/citation_audit_gbt7714.md`，检查阅读状态、source locator、顺序编码、参考文献孤儿、中文参考文献英译和 DOI/URL 问题。
20. **汇报与返修**: 组会/文献汇报材料放 `presentations/`，审稿回复放 `review_response/`。
21. **完整性检查**: 用 `make_passport.py` 固化所有关键文件的 hash、运行命令和输出清单。
22. **排版与投稿包**: 已检测到本机有 `pandoc`，可把 Markdown 转 DOCX；运行 `make submission-package PROJECT=<slug>` 生成主文稿、引用审计、数据/AI 声明、图件和完整性材料的投稿包。
23. **归档**: 项目完成后，保留 `passport/`、`submission_package/`、`manuscript/`、`figures/final/`、`data/processed/` 和关键 Obsidian 笔记。

## 中文投稿命令

```bash
# 查看旧项目缺哪些新模板文件，不写入
make backfill PROJECT=starter_project

# 实际补齐旧项目缺失模板，不覆盖已有文件
make backfill PROJECT=starter_project APPLY=1

# 检查 GB/T 7714、正文引用和中文参考文献英译
make citation-audit PROJECT=starter_project

# 生成《图书情报工作》投稿包
make submission-package PROJECT=starter_project
```

## CNKI 导入命令

```bash
# 先检查导出文件能否解析，不写入文献矩阵
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug> DRY=1

# 确认后写入 library/literature_matrix.csv
make import-cnki INPUT=library/cnki_exports/<file> TAG=<project_slug>

# 生成 5-7 篇前沿候选和研讨问题
make cnki-frontier TAG=<project_slug> TOPIC="生成式人工智能与知识服务"

# 为某一篇生成单篇研讨卡
make paper-brief CITEKEY=<citekey>

# 有合法全文后生成 source-grounded reader，不自动标记 human-read
make paper-reader PROJECT=<project_slug> CITEKEY=<citekey> PDF=library/pdfs/<paper>.pdf

# 检查 metadata-only / 未读文献是否被误用为论文证据
make evidence-gate PROJECT=<project_slug>

# 严格模式：存在证据或引用 ERROR 时失败退出
make evidence-gate PROJECT=<project_slug> STRICT=1
make submission-package PROJECT=<project_slug> STRICT=1
```

## Typora 预览入口

```bash
make typora FILE=README.md
make typora FILE=vault/Home.md
make typora-project PROJECT=starter_project DOC=dashboard
make typora-project PROJECT=starter_project DOC=paper
make typora-project PROJECT=starter_project DOC=claims
```

常用 `DOC` 值：`dashboard`、`rq`、`literature`、`experiment`、`results`、`claims`、`readiness`、`paper`、`terms`、`polishing`、`response`。

## 上下文压缩入口

为了避免每日原始日志越积越大，工作流采用 hot / warm / cold 三层上下文：

- hot：`current_context.md`、`open_loops.md`、`user_model.md`、`context_index.md`。
- warm：每日压缩摘要、当前周总结、最新 context pack。
- cold：原始 daily log 和 file sweep，只在需要精确追溯时读取。

常用命令：

```bash
make codex-compact
make codex-compact DATE=2026-06-19
make codex-compact-all
make codex-context-audit
```

原则：不默认删除原始日志；用压缩摘要和索引减少启动读取量，把跨天真正有用的事实提升进 `current_context.md`。

## 备份与体检入口

关键命令：

```bash
make workflow-backup DATE=2026-06-29 NOTE="daily closeout"
make workflow-audit DATE=2026-06-29
make workflow-refresh DATE=2026-06-29 NOTE="daily closeout"
make workflow-refresh-git DATE=2026-06-29 NOTE="daily closeout"
make git-snapshot DATE=2026-06-29 NOTE="manual snapshot" PUSH=1
```

浏览器入口：

- `workflow_health.html`: 工作流体检页，检查可用性、链接、镜像页、图谱、复习队列、备份和上下文压缩。
- `backups/index.html`: 关键研究状态备份索引。

备份范围偏轻量：脚本、文档、配置、Obsidian Markdown/CSV、项目 Markdown、核心 HTML 入口和文献矩阵会进入备份；PDF、CAJ、原始数据、缓存和大型二进制文件默认排除。Git 远程用于保存这些文本资产的历史版本和异地副本，zip 备份用于本地关键状态快照。

## 重要原则

- 只下载开放获取或你有合法访问权限的 PDF。
- 所有图表必须能追溯到数据、脚本和运行记录。
- 不把未公开论文、原始数据或受试者数据上传到外部服务。
- 每条关键论文论断都需要能指向文献、数据或实验结果。
- AI 可以辅助总结和写作，但你需要保留人工阅读、判断和复核记录。
