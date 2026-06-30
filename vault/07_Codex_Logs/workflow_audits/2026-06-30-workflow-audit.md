# Workflow Audit - 2026-06-30

Generated: 2026-06-30T22:11:08
Summary: PASS=12 WARN=3 FAIL=0

## Checks

| Area | Status | Check | Detail |
|---|---:|---|---|
| 入口/归档 | PASS | 必需入口和今日归档齐全 | 12 个关键文件存在。 |
| 易用性 | PASS | 用户入口没有裸 Markdown 直链 | 主入口、今日页、知识卡、复习、图谱、搜索和日志入口都指向可浏览页面。 |
| 链接健康 | PASS | HTML 本地链接均可解析 | 检查 96 个 HTML 页面。 |
| 镜像页 | PASS | HTML 镜像与源文件同步 | 检查 70 个镜像页。 |
| 知识图谱 | PASS | 图谱入口是可视化关系图 | nodes=113, unique_edges=193 |
| 资产清单 | PASS | artifact manifest 覆盖核心展示资产 | 104 条；display_types=23 |
| 搜索索引 | PASS | 搜索索引和搜索页可用 | 104 条；layers=4 |
| 复习状态 | PASS | 复习状态快照与队列一致 | total=13, due=8, focus=8 |
| 项目状态 | PASS | 项目状态文件可供自动化读取 | 2 个项目。 |
| 复习队列 | WARN | 存在到期复习项 | 8 项到期：方向链；Hook Model 上瘾模型；SICAS模型；软营销；沉浸式内容；用户感知价值；DCI传播力指数；描述性账号调查 |
| 备份 | PASS | 最近备份可用 | backups/researchworkflow-critical-20260630-200857.zip，约 2.0 小时前。 |
| Git/异地备份 | WARN | 存在尚未提交的 Git 改动 | 127 个路径待快照： M Makefile； M codex/state/context_index.md； M docs/INTEGRATED_RESEARCH_LEARNING_WORKFLOW.md； M docs/PAPER_READING_OUTPUT_STANDARD.md； M knowledge_cards/index.html； M knowledge_cards/views/concept-7f8a8bb3.html； M knowledge_cards/views/concept-824dc24b.html； M knowledge_cards/views/concept-841db0d5.html |
| Token/记忆 | PASS | 今日 compact summary 可作为默认启动上下文 | vault/07_Codex_Logs/compact_daily/2026-06-30-summary.md，约 319 words。 |
| 文件卫生 | WARN | 工作区存在系统/缓存文件 | .DS_Store=21；__pycache__=3；这些不会进入 file sweep，但可择机清理。 |
| 行动队列 | PASS | 行动队列可用且入口有效 | 13 个开放行动。 |

## Recommended Daily Order

1. Use `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE="daily closeout"` when remote Git backup is desired.
2. Use `make workflow-refresh DATE=<YYYY-MM-DD> NOTE="daily closeout"` for local-only refresh.
3. Use `make workflow-backup-prune KEEP=30` only when you intentionally want to reduce local backup zips.

Both refresh commands are sequential no-race closeout commands; do not parallelize dashboard generation and audit.

