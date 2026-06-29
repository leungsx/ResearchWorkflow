# Context Pack - 2026-06-18

## Current Research State

用户正在搭建以 Codex 为主入口的科研工作流。目标是把文献检索、论文阅读、PDF 管理、文献摘要、论文写作、排版、科研图、Python/R/MATLAB/Gephi 计算绘图、Obsidian 知识库和长期上下文管理连接起来。

当前已经完成基础工作流和 Codex-first 协作层。后续所有科研对话应默认读取 `codex/OPERATING_PROTOCOL.md`，并维护 daily log、weekly review、context pack、user model 和 open loops。

## Active Projects

- `starter_project`: 模板/示例项目，不是真实研究项目。
- 尚未创建具体研究主题项目。

## Key Files

- `/Users/leung/AGENTS.md`
- `/Users/leung/ResearchWorkflow/README.md`
- `/Users/leung/ResearchWorkflow/codex/OPERATING_PROTOCOL.md`
- `/Users/leung/ResearchWorkflow/codex/state/current_context.md`
- `/Users/leung/ResearchWorkflow/codex/state/open_loops.md`
- `/Users/leung/ResearchWorkflow/codex/state/user_model.md`
- `/Users/leung/ResearchWorkflow/docs/USABILITY_REVIEW.md`
- `/Users/leung/ResearchWorkflow/scripts/codex_archive.py`

## Key Decisions

- 用户主要通过 Codex 进行科研讨论和研究。
- 用户不负责手动整理文件、文献、每日记录或每周总结。
- Codex 在活跃会话内负责归档、分类、上下文压缩、开放问题管理和用户模型更新。
- Codex 不能在没有会话运行时自主定时工作；这个边界必须明确。
- 每次研究会话启动时优先运行 `make codex-start`。

## Literature State

- 已建立 OpenAlex 检索脚本、OA PDF 下载脚本、PDF 文本提取脚本、文献矩阵导入脚本和 Obsidian 文献卡片脚本。
- 尚未针对真实研究主题执行文献检索。

## Experiment / Data State

- Python、Rscript、Pandoc、Gephi 已检测可用。
- MATLAB、Tectonic 未检测到。
- 实验运行记录器可生成 command/stdout/stderr/run_report/environment。
- 数据治理模板尚未补齐。

## Writing / Figure State

- 已有通用 manuscript 模板。
- 已有 Gephi 网络图流程文档。
- 科研图规范已有基础版，仍需要和具体期刊/论文类型适配。

## Open Loops

- 接入 MATLAB。
- 接入 Tectonic 或其他 LaTeX PDF 编译器。
- 补数据治理层。
- 补期刊适配和引用格式层。
- 补系统性综述/PRISMA 模式。
- 补 Obsidian Dataview 查询。
- 补项目 readiness score。
- 在真实项目中检验 Codex-first 归档流程。

## User Preferences

- 中文交流。
- 希望 Codex 主动整理、归档、总结、分类和改进。
- 不希望自己手工维护文件和记录。
- 偏好端到端、可执行、可持续使用的科研系统。
- 希望助手学习并适应其提问方式，提高学习和科研效率。

## Next Recommended Actions

- 继续完善数据治理模板和 readiness score。
- 用户给出真实研究方向后，先收敛研究问题，再进入文献检索。
- 每次科研会话结束前更新 daily log、context pack、open loops 和 user model。
