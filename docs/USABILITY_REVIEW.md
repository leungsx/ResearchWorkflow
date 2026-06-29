# 工作流可用性评审

评审视角：使用者每天能不能低摩擦地推进科研，而不是系统理论上能不能覆盖所有环节。

## P0: 影响日常使用的核心问题

### 1. 缺少单一日常入口

问题：原始版本有 README、SOP、脚本和项目模板，但没有一个命令告诉使用者“这个项目现在做到哪一步、缺什么、下一步做什么”。

已改进：

- 新增 `scripts/project_status.py`
- 新增 `make status PROJECT=<slug>`
- 新增项目级 `00_project_dashboard.md`

### 2. 文献检索结果没有稳定进入文献矩阵

问题：检索 CSV、BibTeX、Obsidian 笔记和 `literature_matrix.csv` 之间缺少桥接，长期会造成“检索过但没有进入知识系统”的散落状态。

已改进：

- 新增 `scripts/import_search_to_matrix.py`
- 新增 `make import-matrix CSV=<search_csv>`

待完善：

- 支持只导入选中的 citekey。
- 支持按项目 tag 自动生成项目内文献清单。

### 3. BibTeX 全局库有被覆盖风险

问题：每次检索都写入全局 `library/bib/references.bib`，会覆盖之前的搜索结果。

已改进：

- 每次检索生成同名 `.bib`
- 全局 `references.bib` 只追加新 citekey

## P1: 影响科研质量和复现的中高优先级问题

### 4. 实验记录还不够完整

问题：原始运行记录有命令、stdout、stderr 和返回码，但缺少环境快照。

已改进：

- `run_experiment.py` 新增 `environment.json`

待完善：

- Python 环境记录 `pip freeze` 或 `conda env export`
- R 环境记录 `sessionInfo()`
- MATLAB 环境记录版本和 toolbox
- 记录输入数据 hash 和输出文件 hash

### 5. 缺少数据治理规范

问题：已有 raw/interim/processed 目录，但还没有数据字典、变量表、敏感数据规则、缺失值规则。

建议新增：

- `data_dictionary.csv`
- `codebook.md`
- `docs/DATA_GOVERNANCE.md`

### 6. 缺少投稿/期刊适配层

问题：现在只有通用论文模板，没有目标期刊格式、字数、引用风格、图表规格和 reporting checklist。

建议新增：

- `projects/<slug>/journal_target.md`
- APA/IEEE/Chicago/GB/T 7714 等引用样式选择
- Pandoc DOCX 模板
- LaTeX 模板和 PDF 编译配置

### 7. 缺少系统性文献综述模式

问题：目前适合普通论文工作流，但如果要做 systematic review/meta-analysis，还需要 PRISMA 流程、纳排标准、筛选记录、偏倚风险表。

建议新增：

- `screening_decisions.csv`
- `prisma_flow.md`
- `risk_of_bias.csv`
- `extraction_form.csv`

## P2: 提升体验和自动化的后续增强

### 8. Obsidian 集成还偏静态

建议新增：

- Dataview 查询模板
- 文献、概念、方法、项目之间的自动 backlink 规范
- 每日科研日志模板
- 项目主页自动汇总核心文献和实验运行

### 9. 缺少备份和版本管理策略

建议：

- 用 Git 管理代码、模板、文稿和小型 CSV
- 大型数据和 PDF 不进 Git
- 定期把 `projects/<slug>/passport/`、`manuscript/`、`figures/final/` 备份到外部位置

### 10. 缺少 GUI/菜单化入口

建议：

- 增加 `scripts/rw.py` 作为统一命令入口
- 或提供简单 TUI 菜单：新建项目、看状态、检索文献、导入矩阵、生成 passport

### 11. 缺少质量评分仪表盘

建议：

- 给每个项目输出 0-100 的 readiness score
- 分项评分：RQ、文献、数据、实验、图表、论文、完整性

### 12. 缺少团队协作规范

建议：

- 作者贡献表
- 决策日志
- 版本命名规范
- 导师/合作者反馈处理表

