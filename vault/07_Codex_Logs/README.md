# Codex Daily Logs

这里保存 Codex 科研会话的每日日志。用户不需要手动维护；Codex 在科研会话中负责追加记录。

## Context Budget Policy

- `daily/`: 原始每日日志，作为冷存档保留，用于精确追溯。
- `compact_daily/`: 每日压缩摘要，作为 warm context，只在需要了解某天内容时读取。
- `file_sweeps/`: 文件活动扫描，默认不读，只有做审计或追踪文件变化时读取。

默认启动时优先读：

1. `codex/state/current_context.md`
2. `codex/state/open_loops.md`
3. `codex/state/user_model.md`
4. `codex/state/context_index.md`

不要默认扫描旧 raw daily logs。
