# Workflow Audit - 2026-07-03

Generated: 2026-07-03T09:32:49
Audit mode: `readonly`
Pre-refresh state hash: `305842f411248bcb1aa40287b08aded7a8d3c0cb8ec4d2aaccb9172ad912c329`
Post-refresh state hash: `305842f411248bcb1aa40287b08aded7a8d3c0cb8ec4d2aaccb9172ad912c329`
Summary: PASS=16 WARN=2 FAIL=0

## Checks

| Area | Status | Check | Detail |
|---|---:|---|---|
| 入口/归档 | PASS | 必需入口和今日归档齐全 | 14 个关键文件存在。 |
| 易用性 | PASS | 用户入口没有裸 Markdown 直链 | 主入口、今日页、知识卡、复习、图谱、搜索和日志入口都指向可浏览页面。 |
| 链接健康 | PASS | HTML 本地链接均可解析 | 检查 130 个 HTML 页面。 |
| 镜像页 | PASS | HTML 镜像与源文件同步 | 检查 98 个镜像页。 |
| 知识图谱 | PASS | 图谱入口是可视化关系图 | nodes=147, unique_edges=466 |
| 资产清单 | PASS | artifact manifest 覆盖核心展示资产 | 144 条；display_types=32 |
| 搜索索引 | PASS | 搜索索引和搜索页可用 | 144 条；layers=4 |
| 复习状态 | PASS | 复习状态快照与队列一致 | total=29, due=5, focus=5 |
| 项目状态 | PASS | 项目状态文件可供自动化读取 | 2 个项目。 |
| 复习队列 | WARN | 存在到期复习项 | 5 项到期：传播力评价；平台互动-服务触达-阅读转化；熵权法；爆款指数；图书馆短视频内容质量评价 |
| 备份 | WARN | 最近备份超过 36 小时 | backups/researchworkflow-critical-20260701-200737.zip，约 37.4 小时前。 |
| Git/异地备份 | PASS | Git 本地和远程快照状态正常 | upstream=origin/main；last commit: 56df06d 2026-07-03 09:32:14 +0800 Refresh workflow state after UI update |
| Token/记忆 | PASS | 今日 compact summary 可作为默认启动上下文 | vault/07_Codex_Logs/compact_daily/2026-07-03-summary.md，约 107 words。 |
| 文件卫生 | PASS | 未发现常见系统/缓存文件 | 工作区较干净。 |
| Schema | PASS | 核心机器状态 schema 校验通过 | 15 个文件通过校验。 |
| 行动队列 | PASS | 行动队列可用且入口有效 | 11 个开放行动。 |
| 项目协作层 | PASS | 项目协作层可用 | 2 个项目；user_waiting=3。 |
| 自动归档策略 | PASS | 自动归档策略可用 | backup=7, prune=0, cache=0 |

## Recommended Daily Order

1. Use `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE="daily closeout"` when remote Git backup is desired.
2. Use `make workflow-refresh DATE=<YYYY-MM-DD> NOTE="daily closeout"` for local-only refresh.
3. Use `make workflow-backup-prune KEEP=30` only when you intentionally want to reduce local backup zips.

Both refresh commands are sequential no-race closeout commands; do not parallelize dashboard generation and audit.

