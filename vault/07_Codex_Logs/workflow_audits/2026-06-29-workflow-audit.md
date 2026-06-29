# Workflow Audit - 2026-06-29

Generated: 2026-06-29T23:03:24
Summary: PASS=8 WARN=2 FAIL=0

## Checks

| Area | Status | Check | Detail |
|---|---:|---|---|
| 入口/归档 | PASS | 必需入口和今日归档齐全 | 10 个关键文件存在。 |
| 易用性 | PASS | 用户入口没有裸 Markdown 直链 | 主入口、今日页、知识卡、图谱和日志入口都指向可浏览页面。 |
| 链接健康 | PASS | HTML 本地链接均可解析 | 检查 29 个 HTML 页面。 |
| 镜像页 | PASS | HTML 镜像与源文件同步 | 检查 20 个镜像页。 |
| 知识图谱 | PASS | 图谱入口是可视化关系图 | nodes=96, unique_edges=98 |
| 复习队列 | WARN | 存在到期复习项 | 2 项到期：方向链；Hook Model 上瘾模型 |
| 备份 | PASS | 最近备份可用 | backups/researchworkflow-critical-20260629-230316.zip，约 0.0 小时前。 |
| Git/异地备份 | PASS | Git 本地和远程快照状态正常 | upstream=origin/main；last commit: 7e5915e 2026-06-29 23:03:21 +0800 workflow snapshot 2026-06-29 |
| Token/记忆 | PASS | 今日 compact summary 可作为默认启动上下文 | vault/07_Codex_Logs/compact_daily/2026-06-29-summary.md，约 336 words。 |
| 文件卫生 | WARN | 工作区存在系统/缓存文件 | .DS_Store=21；__pycache__=2；这些不会进入 file sweep，但可择机清理。 |

## Recommended Daily Order

1. `make obsidian-graph`
2. `make learning-dashboard`
3. `make workflow-backup` when user-facing or evidence state changed
4. `make workflow-audit`

Use `make workflow-refresh` for the sequential no-race version of this closeout.

