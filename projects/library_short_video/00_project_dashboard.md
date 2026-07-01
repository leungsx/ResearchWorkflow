# Project Dashboard - 图书馆短视频相关研究

Last updated: 2026-07-01

## 一句话进度

这个项目已经从“准备检索”推进到“真实 CNKI 检索 + 授权全文组织 + 每日推荐 + 8 篇文献带读 + 3 篇正式 HTML 精读”。现在最重要的不是再堆功能，而是把 SICAS、AARRR 和数字阅读推广服务转化三条线收敛成清晰研究问题和指标草图。

## 当前状态

| 模块 | 状态 | 位置 |
|---|---|---|
| CNKI 检索计划 | 已有 | [cnki_search_plan.md](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/cnki_search_plan.md) |
| CNKI 检索结果/入库 | 项目矩阵 60 条；CNKI 检索结果曾刷新到 914 条 | [literature_matrix.csv](/Users/leung/ResearchWorkflow/library/literature_matrix.csv) |
| Fast-lane 快速快照 | 已建立；用于下一篇推荐/状态查询，减少小任务联动修改 | [library_short_video_fast_snapshot.md](/Users/leung/ResearchWorkflow/codex/runtime/library_short_video_fast_snapshot.md) |
| 授权全文 | 8 篇已组织 | [PDF 文件夹](/Users/leung/ResearchWorkflow/library/pdfs/library_short_video/) |
| CAJ 转 PDF | 当前学习集已跑通 | [CAJ 转换记录](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/caj_conversion/) |
| Reader | 8/8 已生成 | [readers](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/readers/README.md) |
| 论文上下文包 | 已读 7 篇已生成，用于省 token 带读 | [context_packs](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/context_packs/) |
| 今日推荐 | 2026-07-01 主读已完成张承 2021 数字阅读推广服务转化论文精读，下一步继续补传播力评价候选 | [今日精读入口](/Users/leung/ResearchWorkflow/paper_reading/today.html) |
| 今日阅读看板 | 已建立 | [reading_board.md](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/reading_board.md) |
| 5 篇快速复盘 | 已生成 | [2026-06-20-five-paper-quick-recap.md](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/recaps/2026-06-20-five-paper-quick-recap.md) |
| 创新/局限/机会台账 | 8 张卡片 | [innovation_limitation_bank.md](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/innovation_limitation_bank.md) |
| 文献综述工作台 | 已建立；今日补入张承 2021 深读，用于把平台互动推进到数字阅读推广服务价值 | [literature_review_workbench.md](/Users/leung/ResearchWorkflow/projects/library_short_video/literature/literature_review_workbench.md) |
| 文献综述 | 已开始形成主线 | [03_literature_synthesis.md](/Users/leung/ResearchWorkflow/projects/library_short_video/03_literature_synthesis.md) |
| 证据门禁 | ERROR=0, WARN=0；metadata-only 候选只保留在补读/检索语境 | [evidence_gate_report.md](/Users/leung/ResearchWorkflow/projects/library_short_video/manuscript/evidence_gate_report.md) |

## 当前阅读进度

| 状态 | 篇数 | 含义 |
|---|---:|---|
| `skimmed` | 8 | Codex 已带读并写入 reader notes/研讨卡/综述/台账，但还不是人工逐页核验 |
| `metadata-only` | 52 | 只在候选池或尚未读完，不能作为论文主张证据 |
| `human-read` | 0 | 需要你确认已经认真读过 |
| `verified` | 0 | 需要原文页码/证据完全核验后才能标 |

## 项目流程图

```mermaid
flowchart TD
    A[CNKI 检索: 图书馆 * 短视频] --> B[文献矩阵 60 条]
    B --> C[每日推荐 1+3]
    C --> D[研讨卡: 快速判断]
    C --> K[上下文包: 省 token 带读]
    C --> E[Reader: 证据块精读]
    K --> F[Reading Notes]
    E --> F[Reading Notes]
    F --> G[文献综述]
    F --> H[创新-局限-机会台账]
    G --> L[文献综述工作台]
    H --> L
    L --> I[候选研究方向]
    I --> J[研究问题/方法设计]
```

## 下一步建议

1. 默认以“图书馆短视频互动如何连接数字阅读推广服务价值”为主问题。
2. 把 [[SICAS模型]]、[[AARRR 漏斗模型]] 和 [[数字阅读推广]] 对齐成“用户路径 + 阶段指标 + 服务动作”指标草图。
3. 继续补读传播力评价或 2023 后多平台研究；metadata-only 候选只作为补读方向，不进入论文主张。
4. 如果准备写论文，先不要直接写正文；先把文献综述工作台、`01_research_question.md` 和 `03_literature_synthesis.md` 对齐为 1 个主问题 + 2 个子问题。

## 你可以直接说

- `打开今日阅读看板，告诉我这 7 篇已经读出了什么。`
- `基于上下文包，帮我快速复盘 7 篇已读论文。`
- `打开 5 篇快速复盘，再结合今天新增 2 篇帮我判断最值得做的研究方向。`
- `打开文献综述工作台，帮我整理阶段性论文工作总结。`
- `用 7 篇已读文献帮我收敛 3 个研究问题。`
- `继续读剩下两篇 reader。`
- `打开创新局限台账，帮我找最值得做的改进点。`
- `检查这个项目距离写论文还缺什么。`

## 快捷命令

```bash
make status PROJECT=library_short_video
make fast-status PROJECT=library_short_video TOPIC="图书馆短视频相关研究" PRINT=1
make typora-project PROJECT=library_short_video DOC=reading
make lit-workbench PROJECT=library_short_video
make typora-project PROJECT=library_short_video DOC=contextpacks
make paper-context PROJECT=library_short_video ALL=1
make typora-project PROJECT=library_short_video DOC=insights
make evidence-gate PROJECT=library_short_video
```
