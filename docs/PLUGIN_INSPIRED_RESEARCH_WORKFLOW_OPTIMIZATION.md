# 插件启发的科研工作流优化

Last updated: 2026-06-20

本说明来自对本机 `.codex/.tmp/plugins/plugins/` 插件缓存的筛选。这里不是直接启用外部账号型插件，而是把适合科研工作流的产品设计模式迁移成本地 Markdown、脚本和看板。

## 结论

当前最值得迁移的不是某一个插件，而是这些模式：

| 插件/类型 | 可借鉴能力 | 已迁移到本工作流的形式 |
|---|---|---|
| Notion research documentation | 先选输出格式：quick brief、research summary、comparison、comprehensive report | 论文阅读产物分层：研讨卡、上下文包、Reader、综述 |
| Notion knowledge capture | 把对话、决策、FAQ、how-to 固化成可链接页面 | Home、阅读看板、创新-局限台账、daily log |
| Zotero | 本地文献库、引用键、BibTeX、只在明确需要时读取全文 | 继续保留 `literature_matrix.csv` + citekey；未来可接 Zotero |
| Scite / Hebbia | 研究回答必须显示证据、争议和缺口 | Evidence gate、source block ID、上下文包的核心证据快照 |
| Readwise / Reader | 高亮和阅读材料可被语义搜索、复盘和再次利用 | 论文带读上下文包、Reader Reading Notes、研讨卡 |
| Read AI / Otter / Fireflies | 摘要、关键问题、行动项从长文本中分离 | 每篇论文沉淀“核心观点、研讨问题、下一步行动” |
| Glean / Mem | 把第二大脑作为 AI 的检索上下文 | Obsidian vault、Home、context packs、context index |
| CircleCI cache/chunk | 分块、缓存、只加载有用上下文，避免重复传输 | `paper-context` 命令；先读小包，必要时再读完整 Reader |
| OpenAI Developers | 可把成熟流程封装为插件/小应用 | 后续可把科研首页、阅读看板、文献推荐做成可交互本地应用 |

## 已完成的本地改进

### 1. 论文带读上下文包

新增命令：

```bash
make paper-context PROJECT=library_short_video CITEKEY=<citekey>
make paper-context PROJECT=library_short_video ALL=1
```

输出位置：

```text
projects/library_short_video/literature/context_packs/
```

用途：

- 共读时优先加载小包，减少反复读取完整 Reader 的 token 消耗。
- 小包包含：元数据、Reading Notes、研讨卡核心理解、创新-局限摘录、核心证据 block 快照、带读顺序。
- 需要核验证据时再打开完整 Reader 和原文。

### 2. 四层阅读产物

| 层级 | 文件 | 作用 |
|---|---|---|
| 阅读看板 | `literature/reading_board.md` | 用户入口：今天读什么、去哪里读、读完看什么 |
| 上下文包 | `literature/context_packs/<citekey>.md` | Codex 带读优先加载，省 token |
| 研讨卡 | `vault/15_CNKI_Frontier/paper_briefs/<citekey>.md` | 判断论文价值、角色、问题和讨论路线 |
| Reader | `literature/readers/<citekey>/paper.md` | source-grounded 全文块、证据追溯和精读材料 |

### 3. Reader 和研讨卡职责拆分

- Reader 不再承担所有功能。它主要负责保存源文本、block ID、Reading Notes 和证据边界。
- 研讨卡负责“这篇论文为什么值得读、如何讨论、对项目有什么用”。
- 上下文包负责“让 Codex 带读时少读冗余全文”。
- 创新-局限台账负责“从论文中沉淀未来研究机会”。

## 暂不直接启用的插件

| 插件 | 暂不直接启用原因 | 后续条件 |
|---|---|---|
| Zotero | 需要确认本机 Zotero 使用习惯和本地 API | 用户希望将 CNKI 文献同步到 Zotero 时再接 |
| Scite | 外部服务，中文 CNKI 覆盖可能有限 | 用于英文文献或国际引文语境时再评估 |
| Readwise | 需要外部账号和阅读库 | 若用户已有 Readwise/Reader，再做高亮同步 |
| Notion/Mem/Glean | 用户当前主知识库是本地 Obsidian/Markdown | 只有用户明确想同步 Notion/Mem 时再接 |

## 下一步可优化

1. 给 `paper_reader.py` 增加自动生成上下文包的选项。
2. 给每日推荐报告自动附上上下文包链接。
3. 做一个“阅读复盘面板”：按论文、理论、方法、创新、局限、机会编号聚合。
4. 如果多个项目并行，自动刷新每个项目的 reading board。
5. 后续考虑把科研首页做成一个本地网页应用或 Codex plugin。
