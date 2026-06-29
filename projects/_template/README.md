# {{PROJECT_TITLE}}

Project slug: `{{PROJECT_SLUG}}`

## Project Map

- `01_research_question.md`: 研究问题、范围和贡献。
- `00_project_dashboard.md`: 当前阶段、下一步和阶段清单。
- `02_methodology.md`: 方法、数据、变量和识别策略。
- `03_literature_synthesis.md`: 文献综合。
- `04_experiment_plan.md`: 实验、统计或仿真方案。
- `05_hypothesis_registry.md`: 可检验猜想。
- `06_result_interpretation.md`: 结果解释。
- `07_claim_evidence_map.md`: 主张-证据映射。
- `08_publication_readiness.md`: 投稿、汇报或返修前的成熟度检查。
- `analysis/`: Python、R、MATLAB 脚本。
- `data/`: raw/interim/processed 数据。
- `data/data_dictionary.md`: 数据字段、来源、缺失值和可用性说明。
- `data/codebook.md`: 质性编码、内容分析或人工标注规则。
- `data/data_governance.md`: 数据权限、隐私、共享和 AI 使用边界。
- `figures/`: 图表规格、草图和最终图。
- `literature/readers/`: 重要论文的 source-grounded 精读包。
- `manuscript/`: 中文论文正文、引用、目标期刊 profile、术语表、润色记录、AI 使用披露和投稿检查清单。
- `presentations/`: 组会、journal club、论文汇报 PPT 计划和产物。
- `review_response/`: 审稿意见、逐点回复和返修 tracker。
- `passport/`: 运行记录、hash 和完整性检查。
- `submission_package/`: 由 `make submission-package PROJECT={{PROJECT_SLUG}}` 生成的投稿包，不需要手工新建。

## Daily Start

```bash
cd /Users/leung/ResearchWorkflow
make status PROJECT={{PROJECT_SLUG}}
```

## Pre-Submission Commands

```bash
make evidence-gate PROJECT={{PROJECT_SLUG}}
make citation-audit PROJECT={{PROJECT_SLUG}}
make submission-package PROJECT={{PROJECT_SLUG}}

# Strict mode fails when evidence/citation ERROR issues remain.
make submission-package PROJECT={{PROJECT_SLUG}} STRICT=1
```

## Full-Paper Reader

```bash
make paper-reader PROJECT={{PROJECT_SLUG}} CITEKEY=<citekey> PDF=<authorized_pdf>
```
