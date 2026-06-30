# Workflow Audit - 2026-06-30

Generated: 2026-06-30T22:36:26
Summary: PASS=14 WARN=2 FAIL=0

## Checks

| Area | Status | Check | Detail |
|---|---:|---|---|
| 入口/归档 | PASS | 必需入口和今日归档齐全 | 12 个关键文件存在。 |
| 易用性 | PASS | 用户入口没有裸 Markdown 直链 | 主入口、今日页、知识卡、复习、图谱、搜索和日志入口都指向可浏览页面。 |
| 链接健康 | PASS | HTML 本地链接均可解析 | 检查 96 个 HTML 页面。 |
| 镜像页 | PASS | HTML 镜像与源文件同步 | 检查 70 个镜像页。 |
| 知识图谱 | PASS | 图谱入口是可视化关系图 | nodes=113, unique_edges=193 |
| 资产清单 | PASS | artifact manifest 覆盖核心展示资产 | 105 条；display_types=24 |
| 搜索索引 | PASS | 搜索索引和搜索页可用 | 105 条；layers=4 |
| 复习状态 | PASS | 复习状态快照与队列一致 | total=13, due=8, focus=8 |
| 项目状态 | PASS | 项目状态文件可供自动化读取 | 2 个项目。 |
| 复习队列 | WARN | 存在到期复习项 | 8 项到期：方向链；Hook Model 上瘾模型；SICAS模型；软营销；沉浸式内容；用户感知价值；DCI传播力指数；描述性账号调查 |
| 备份 | PASS | 最近备份可用 | backups/researchworkflow-critical-20260630-200857.zip，约 2.5 小时前。 |
| Git/异地备份 | PASS | Git 本地和远程快照状态正常 | upstream=origin/main；last commit: 48db7d6 2026-06-30 22:36:08 +0800 fix workflow state git dirty baseline |
| Token/记忆 | PASS | 今日 compact summary 可作为默认启动上下文 | vault/07_Codex_Logs/compact_daily/2026-06-30-summary.md，约 319 words。 |
| 文件卫生 | WARN | 工作区存在系统/缓存文件 | .DS_Store=21；__pycache__=3；这些不会进入 file sweep，但可择机清理。 |
| Schema | PASS | 核心机器状态 schema 校验通过 | 8 个文件通过校验。 |
| 行动队列 | PASS | 行动队列可用且入口有效 | 12 个开放行动。 |

## Recommended Daily Order

1. Use `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE="daily closeout"` when remote Git backup is desired.
2. Use `make workflow-refresh DATE=<YYYY-MM-DD> NOTE="daily closeout"` for local-only refresh.
3. Use `make workflow-backup-prune KEEP=30` only when you intentionally want to reduce local backup zips.

Both refresh commands are sequential no-race closeout commands; do not parallelize dashboard generation and audit.

