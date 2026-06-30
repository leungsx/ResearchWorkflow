# Context Pack - 2026-06-30

## Current Research State

- 新增 CNKI 人工下载交接流程：Codex 生成检索/下载清单和 incoming 文件夹，用户合法下载全文，Codex 再验收、入库、建 Reader、推荐分析。

## Active Projects

- `library_short_video`: 当前主项目，今日已生成 12 篇直接相关的 CNKI 全文补库清单。

## Key Files

- `scripts/cnki_human_download_handoff.py`
- `docs/CNKI_WORKFLOW.md`
- `docs/CNKI_DAILY_LEARNING.md`
- `projects/library_short_video/literature/cnki_search_plan.md`
- `vault/15_CNKI_Frontier/download_requests/library_short_video/2026-06-30-library_short_video-cnki-download-request.html`
- `vault/15_CNKI_Frontier/download_requests/library_short_video/2026-06-30-library_short_video-cnki-download-request.csv`
- `library/pdfs/library_short_video/incoming/2026-06-30/`

## Key Decisions

- CNKI 补全文默认走人机交接：`make cnki-handoff` 生成清单，用户下载，`make cnki-intake` 验收。
- 默认清单严格过滤，只列核心相关论文；外部比较文献必须显式 `ALLOW_EXTERNAL=1`。
- 用户下载原件默认保留在 incoming 文件夹；intake 复制到稳定库目录，除非显式 `MOVE=1`。
- intake 拒绝伪 PDF，并保留 invalid 状态供用户重新下载。

## Literature State

- 今日下载清单前几篇高优先级候选：
  - `cnki_2021_645f03f388`《图书馆短视频账号传播力研究——以省级公共图书馆为例》
  - `cnki_2021_2bcdca1cf9`《短视频社会化阅读推广效果分析——以抖音短视频为例》
  - `cnki_2021_c7cfb20665`《我国省级公共图书馆抖音短视频运营现状调查分析》
  - `cnki_2021_4d1ed48a48`《短视频时代图书馆知识营销模式构建研究》
  - `cnki_2021_9747478bfb`《我国副省级及以上公共图书馆的短视频应用现状——以抖音为中心的调查》

## Experiment / Data State

- `make cnki-handoff PROJECT=library_short_video TOPIC="图书馆短视频相关研究" COUNT=12 DATE=2026-06-30` 已成功。
- `make cnki-intake PROJECT=library_short_video REQUEST=...` 已在空 incoming 文件夹上测试，Stored=0、Invalid=0。
- 目标下载文件夹当前为空：`library/pdfs/library_short_video/incoming/2026-06-30/`。

## Writing / Figure State

- 无正式写作更新。

## Open Loops

- 用户尚未按清单下载全文。
- 下载后需要运行 `make cnki-intake PROJECT=library_short_video BUILD_READERS=1`。
- 若有 CAJ/KDH/NH，需要运行 `make caj-convert PROJECT=library_short_video SCAN=1`。
- 可考虑下一轮把最新 CNKI 下载清单作为 dashboard 的可视化入口。

## User Preferences

- 用户希望 CNKI 获取流程可控、可见、低黑箱：Codex 给清单和文件夹，用户下载，Codex 后处理。

## Next Recommended Actions

1. 打开 `vault/15_CNKI_Frontier/download_requests/library_short_video/2026-06-30-library_short_video-cnki-download-request.html`。
2. 在 CNKI 高级检索中按页面列出的检索式搜索。
3. 优先下载前 5-8 篇到 `library/pdfs/library_short_video/incoming/2026-06-30/`。
4. 下载后运行 `make cnki-intake PROJECT=library_short_video BUILD_READERS=1`。
5. 再运行 `make cnki-daily PROJECT=library_short_video TOPIC="图书馆短视频相关研究"` 选下一篇精读。
