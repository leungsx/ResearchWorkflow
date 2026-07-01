# Workflow Audit - 2026-07-01

Generated: 2026-07-01T08:57:53
Summary: PASS=16 WARN=2 FAIL=0

## Checks

| Area | Status | Check | Detail |
|---|---:|---|---|
| 入口/归档 | PASS | 必需入口和今日归档齐全 | 14 个关键文件存在。 |
| 易用性 | PASS | 用户入口没有裸 Markdown 直链 | 主入口、今日页、知识卡、复习、图谱、搜索和日志入口都指向可浏览页面。 |
| 链接健康 | PASS | HTML 本地链接均可解析 | 检查 99 个 HTML 页面。 |
| 镜像页 | PASS | HTML 镜像与源文件同步 | 检查 71 个镜像页。 |
| 知识图谱 | PASS | 图谱入口是可视化关系图 | nodes=113, unique_edges=193 |
| 资产清单 | PASS | artifact manifest 覆盖核心展示资产 | 110 条；display_types=28 |
| 搜索索引 | PASS | 搜索索引和搜索页可用 | 110 条；layers=4 |
| 复习状态 | PASS | 复习状态快照与队列一致 | total=13, due=13, focus=12 |
| 项目状态 | PASS | 项目状态文件可供自动化读取 | 2 个项目。 |
| 复习队列 | WARN | 存在到期复习项 | 13 项到期：方向链；Hook Model 上瘾模型；SICAS模型；软营销；沉浸式内容；用户感知价值；DCI传播力指数；描述性账号调查 |
| 备份 | PASS | 最近备份可用 | backups/researchworkflow-critical-20260630-200857.zip，约 12.8 小时前。 |
| Git/异地备份 | PASS | Git 本地和远程快照状态正常 | upstream=origin/main；last commit: 7b1dda4 2026-07-01 08:57:41 +0800 add search collaboration archive workflow layers |
| Token/记忆 | PASS | 今日 compact summary 可作为默认启动上下文 | vault/07_Codex_Logs/compact_daily/2026-07-01-summary.md，约 88 words。 |
| 文件卫生 | WARN | 工作区存在系统/缓存文件 | .DS_Store=21；__pycache__=3；这些不会进入 file sweep，但可择机清理。 |
| Schema | PASS | 核心机器状态 schema 校验通过 | 10 个文件通过校验。 |
| 行动队列 | PASS | 行动队列可用且入口有效 | 12 个开放行动。 |
| 项目协作层 | PASS | 项目协作层可用 | 2 个项目；user_waiting=3。 |
| 自动归档策略 | PASS | 自动归档策略可用 | backup=6, prune=0, cache=24 |

## Recommended Daily Order

1. Use `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE="daily closeout"` when remote Git backup is desired.
2. Use `make workflow-refresh DATE=<YYYY-MM-DD> NOTE="daily closeout"` for local-only refresh.
3. Use `make workflow-backup-prune KEEP=30` only when you intentionally want to reduce local backup zips.

Both refresh commands are sequential no-race closeout commands; do not parallelize dashboard generation and audit.

