# Context Pack - 2026-06-29

## Current Research State

- 当前主项目：`library_short_video` / 图书馆短视频相关研究。
- 今日主读论文：`cnki_2023_34348faa1e`《基于SICAS模型的公共图书馆短视频营销策略研究》。
- 今日已形成完整资产链：论文精读 HTML -> Reader/论文笔记 HTML 镜像 -> 概念/方法卡 -> Obsidian 图谱 CSV -> 可视化图谱入口 -> 复习队列 -> 项目综述工作台。
- 用户已明确要求：以后每日论文精读必须固定使用 HTML-first 呈现方式。

## Active Projects

- `library_short_video`
  - 当前用途：图书馆短视频研究的主项目。
  - 今日贡献：SICAS 五阶段为“平台互动 -> 服务触达 -> 阅读转化/分享回流”提供过程框架。
  - 明日重点：核验 SICAS 论文证据，并把路径转成变量草图。

## Key Files

- 固定入口：`paper_reading/today.html`
- 总览入口：`study_dashboard.html`
- 今日主读页：`paper_reading/2026-06-29-sicas-public-library-short-video.html`
- 今日二级 HTML 镜像：`paper_reading/views/`
- 知识卡入口：`knowledge_cards/index.html`
- 知识卡 HTML 镜像：`knowledge_cards/views/`
- 可视化图谱：`knowledge_graph/index.html`
- 学习日志：`logs/2026-06-29.html`
- 学习日志镜像：`logs/views/`
- 今日 Codex 日志：`vault/07_Codex_Logs/daily/2026-06-29.md`
- 今日文件归类：`vault/07_Codex_Logs/file_sweeps/2026-06-29-file-sweep.md`
- 工作流脚本：`scripts/build_learning_dashboard.py`
- 工作流体检：`workflow_health.html`
- 备份索引：`backups/index.html`
- 最新备份包：`backups/researchworkflow-critical-20260629-223910.zip`

## Key Decisions

- Markdown 是 canonical memory；HTML 是用户默认阅读和复习界面。
- 每日入口固定为 `paper_reading/today.html`，不再依赖用户自己找当天文件。
- 用户侧链接默认指向 HTML 镜像页；本地 `.md` 只作为“打开原始 Markdown”回源按钮。
- 知识图谱默认以交互式 SVG 图谱展示；CSV/table 只用于核对和导出。
- `make learning-dashboard` 承担自动纠偏：扫描每日论文页中的本地 Markdown 链接，生成 HTML 镜像并改链。
- 今天只归档、记录和刷新入口，不删除用户文件，不迁移用途不确定文件。
- 日终维护默认使用 `make workflow-refresh DATE=<date> NOTE="<note>"`，不要并行运行 dashboard/audit 以免产生竞态误报。
- Git/GitHub 接入后，日终维护的远程备份版本是 `make workflow-refresh-git DATE=<date> NOTE="<note>"`；Git 只追踪文本资产和可回溯记录，PDF/CAJ/KDH、zip 备份、缓存、预览图和大型二进制不入 Git。

## Literature State

- `cnki_2023_34348faa1e` 已完成 source-grounded skim 和 HTML 精读页。
- 新增/更新知识卡：
  - `SICAS模型`
  - `沉浸式内容`
  - `软营销`
  - `用户感知价值`
  - `DCI传播力指数`
  - `描述性账号调查`
- 待核验：Reader blocks `B0007-B0016` 对应页码、图表和变量表述。
- 待沉淀：`精神激励` 仍是 linked 节点，尚未成为正式知识卡。

## Experiment / Data State

- `make obsidian-graph` 当前导出 90 nodes / 170 edges。
- `make obsidian-graph` 已修复重复边问题，最近审计显示 96 nodes / 98 unique edges。
- `make learning-dashboard` 已刷新：
  - `study_dashboard.html`
  - `paper_reading/today.html`
  - `paper_reading/index.html`
  - `knowledge_cards/index.html`
  - `knowledge_graph/index.html`
  - `logs/index.html`
  - `paper_reading/views/`
  - `knowledge_cards/views/`
  - `logs/views/`
- `make workflow-audit` 最近状态：PASS=7, WARN=2, FAIL=0。
- `make workflow-backup` 已生成轻量关键状态备份；PDF/CAJ/原始数据/缓存不进入该备份包。
- 入口页 link audit：主要入口页本地 `.md` 直链为 0。
- 私有 GitHub 远程已创建：`https://github.com/leungsx/ResearchWorkflow`。
- 当前 Git 备份策略文件：`docs/GIT_BACKUP_STRATEGY.md`。
- Git 快照脚本：`scripts/git_snapshot.py`，会阻止未忽略的大文件/二进制和未忽略的嵌套 Git 仓库进入提交。

## Writing / Figure State

- 尚未进入正式论文写作。
- 当前最接近写作的材料是 `projects/library_short_video/literature/literature_review_workbench.md` 和 `projects/library_short_video/03_literature_synthesis.md`。
- 下一步应把今天的 SICAS 框架转成“平台互动 -> 服务触达 -> 阅读转化”的变量草图，而不是继续泛泛补文献。

## Open Loops

- SICAS 论文页码/图表核验。
- `精神激励` 知识卡。
- Hook Model 与方向链复习清欠。
- 机会节点动作化：`图书馆短视频服务价值框架`、`SICAS-服务转化路径`、`图书馆短视频多平台复测`。
- 文件归类仅记录，不做删除；后续如果出现孤立 HTML 或旧日志节点，再单独处理。
- 体检 WARN=2：旧复习项到期、工作区存在 `.DS_Store`/`__pycache__`。这两项不是系统阻断问题。
- 如果本地备份包逐渐变多，用 `make workflow-backup-prune KEEP=30` 显式保留最近 30 份；默认不静默删除。

## User Preferences

- 强偏好统一 HTML 入口和可视化界面。
- 不希望每日产物分散在多处，需要“点开就能看”。
- 不喜欢知识图谱只显示表格或 CSV，想看关系图谱本身。
- 需要论文阅读资产可复习、可连接、可转化为研究行动。

## Next Recommended Actions

1. 明早从 `paper_reading/today.html` 进入。
2. 先清欠复习：`Hook Model 上瘾模型`、`方向链`。
3. 回 Reader 核验 `B0007-B0016`。
4. 对照 SICAS / Hook / ELM / AARRR，明确框架分工。
5. 在文献综述工作台起草变量草图。
