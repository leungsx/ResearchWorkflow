# 科研工作流 SOP

如果你是第一次使用，先看 `docs/USER_VISUAL_GUIDE.md`，里面按场景说明了哪些功能已实现、什么时候使用、如何通过 Codex 直接发起。

## 1. 项目启动

每个研究问题或论文单独建一个项目：

```bash
make new SLUG=project_slug TITLE="Project Title"
make status PROJECT=project_slug
```

项目内必须先完成：

- `01_research_question.md`
- `02_methodology.md`
- `04_experiment_plan.md`

## 2. 文献检索

使用 OpenAlex 检索元数据：

```bash
make search Q="your research query"
```

输出会进入 `library/search_results/`，BibTeX 会进入 `library/bib/references.bib`。

把检索结果导入文献矩阵：

```bash
make import-matrix CSV=library/search_results/<file>.csv
```

## 3. PDF 下载与文本提取

只下载开放获取或你有合法访问权限的 PDF：

```bash
make download
make extract
```

## 4. 文献笔记

为关键论文创建 Obsidian 文献卡片：

```bash
/Users/leung/anaconda3/bin/python scripts/add_literature_note.py --csv library/search_results/<file>.csv --citekey Smith2024Example
```

人工阅读后，在文献卡片中标记：

- 是否已人工读完
- 可引用结论
- 方法与数据
- 局限性
- 与本项目的关系

## 5. 实验运行

任何计算、统计或仿真都通过运行记录器启动：

```bash
/Users/leung/anaconda3/bin/python scripts/run_experiment.py --project project_slug --name baseline -- /Users/leung/anaconda3/bin/python analysis/python/analysis.py
/Users/leung/anaconda3/bin/python scripts/run_experiment.py --project project_slug --name r_stats -- Rscript analysis/R/analysis.R
/Users/leung/anaconda3/bin/python scripts/run_experiment.py --project project_slug --name matlab_sim -- matlab -batch "run('analysis/matlab/simulation.m')"
```

脚本会记录命令、环境快照、开始时间、结束时间、stdout、stderr 和返回码。

## 6. 图表生成

每张最终图必须同时具备：

- `figures/final/<figure>.png|pdf|svg`
- `figures/specs/<figure>.md`
- 生成该图的数据文件
- 生成该图的脚本或 notebook

## 7. 论文写作

主稿写在：

```text
projects/<slug>/manuscript/paper.md
```

引用集中维护在：

```text
projects/<slug>/manuscript/references.bib
library/bib/references.bib
```

## 8. 完整性关口

投稿、送审或交给导师前运行：

```bash
make passport PROJECT=project_slug
```

然后检查 `projects/<slug>/passport/material_passport.json`。
