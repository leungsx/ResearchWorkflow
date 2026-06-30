# Workflow Audit - 2026-06-30

Generated: 2026-06-30T08:50:25
Summary: PASS=7 WARN=3 FAIL=0

## Checks

| Area | Status | Check | Detail |
|---|---:|---|---|
| 入口/归档 | PASS | 必需入口和今日归档齐全 | 10 个关键文件存在。 |
| 易用性 | PASS | 用户入口没有裸 Markdown 直链 | 主入口、今日页、知识卡、图谱和日志入口都指向可浏览页面。 |
| 链接健康 | PASS | HTML 本地链接均可解析 | 检查 29 个 HTML 页面。 |
| 镜像页 | PASS | HTML 镜像与源文件同步 | 检查 20 个镜像页。 |
| 知识图谱 | PASS | 图谱入口是可视化关系图 | nodes=100, unique_edges=98 |
| 复习队列 | WARN | 存在到期复习项 | 8 项到期：方向链；Hook Model 上瘾模型；SICAS模型；软营销；沉浸式内容；用户感知价值；DCI传播力指数；描述性账号调查 |
| 备份 | PASS | 最近备份可用 | backups/researchworkflow-critical-20260630-085025.zip，约 0.0 小时前。 |
| Git/异地备份 | WARN | 存在尚未提交的 Git 改动 | 41 个路径待快照： M Makefile； M README.md； M codex/state/context_index.md； M codex/state/current_context.md； M codex/state/user_model.md； M docs/CNKI_DAILY_LEARNING.md； M docs/CNKI_WORKFLOW.md； M knowledge_cards/index.html |
| Token/记忆 | PASS | 今日 compact summary 可作为默认启动上下文 | vault/07_Codex_Logs/compact_daily/2026-06-30-summary.md，约 319 words。 |
| 文件卫生 | WARN | 工作区存在系统/缓存文件 | .DS_Store=21；__pycache__=2；这些不会进入 file sweep，但可择机清理。 |

## Recommended Daily Order

1. Use `make workflow-refresh-git DATE=<YYYY-MM-DD> NOTE="daily closeout"` when remote Git backup is desired.
2. Use `make workflow-refresh DATE=<YYYY-MM-DD> NOTE="daily closeout"` for local-only refresh.
3. Use `make workflow-backup-prune KEEP=30` only when you intentionally want to reduce local backup zips.

Both refresh commands are sequential no-race closeout commands; do not parallelize dashboard generation and audit.

