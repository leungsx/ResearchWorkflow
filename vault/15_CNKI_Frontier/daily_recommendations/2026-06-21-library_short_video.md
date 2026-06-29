# CNKI 每日论文推荐 - 图书馆短视频相关研究

Date: 2026-06-21
Project: `library_short_video`
Stage: `foundation_high_impact` / 基础高影响
Stage logic: 先读领域内被引、下载、来源和贴合度都较强的论文，建立共同语言。
Candidate pool: 20 project-tagged CNKI rows
Profile: `projects/library_short_video/literature/recommendation_profile.json`
State: `projects/library_short_video/literature/daily_learning_state.json`

## 边界

- 这是每日学习推荐，不等同于全文核验。
- `metadata-only`、`skimmed` 不能直接作为论文证据；真正写进论文前必须补足全文阅读和 source locator。
- 原文只使用你通过 CNKI/机构/图书馆合法取得的本地文件。

## 指标来源

- `library/cnki_exports/library_short_video/cnki_library_short_video_current.csv`
- `library/cnki_exports/library_short_video/cnki_library_short_video_current.json`
- `library/cnki_exports/library_short_video/cnki_library_short_video_page1.csv`
- `library/cnki_exports/library_short_video/cnki_library_short_video_page1.json`

## 今日主读

**基于短视频营销的公共图书馆数字阅读推广策略研究**

- Citekey: `cnki_2021_5530e86157`
- 年份/来源: 2021 / 图书馆工作与研究
- 作者: 张承
- CNKI 指标: 被引 99，下载 2915
- 阅读状态: `metadata-only`
- Reader: `projects/library_short_video/literature/readers/cnki_2021_5530e86157/paper.md`
- 本地全文: `library/pdfs/library_short_video/cnki_2021_5530e86157.caj`

### 为什么今天读它

- CNKI 被引 99，下载 2915
- 领域词命中: 公共图书馆、阅读推广、图书馆、短视频、视频
- 核心主题组覆盖: 公共图书馆、短视频
- 图情领域来源
- 可用于现状/问题/策略地图
- 已有 source-grounded reader
- 已有本地授权全文/转换 PDF
- 已有笔记路径

### 今天怎么读

- 先读题名、摘要/引言和结论，确认它为什么成为领域基础文献。
- 再看研究对象、数据来源、指标和方法，判断证据强度。
- 提取 3 个可复用概念或判断框架，以及 2 个明显局限。
- 最后连接到你的问题：它帮助我们理解图书馆短视频的什么核心机制？

### 研讨问题

- 这篇文章真正解决的是图书馆服务问题、传播效果问题，还是平台运营问题？
- 它为什么被引较多：理论框架、数据方法、实践问题，还是选题时机？
- 它把短视频效果测量成什么：观看、点赞、互动、阅读推广、服务触达，还是知识传播？
- 它的证据是否足以支撑结论？哪些地方只是经验判断或策略建议？
- 如果面向《图书情报工作》，它提示我们需要补强哪类图情领域贡献？

### 下一步命令

```bash
make paper-brief CITEKEY=cnki_2021_5530e86157
make insight-bank PROJECT=library_short_video CITEKEY=cnki_2021_5530e86157
```

### 可用资源

- 已可精读 reader: `projects/library_short_video/literature/readers/cnki_2021_5530e86157/paper.md`
- 本地全文: `library/pdfs/library_short_video/cnki_2021_5530e86157.caj`

## 伴读队列

| Rank | Score | Citekey | Year | Title | Source | Cited | Downloads | Reader | PDF | Read status |
|---:|---:|---|---:|---|---|---:|---:|---|---|---|
| 1 | 80.0 | `cnki_2021_3771e58987` | 2021 | 公共图书馆和高校图书馆短视频营销比较研究 | 大学图书馆学报 | 92 | 3214 | no | no | metadata-only |
| 2 | 79.5 | `cnki_2021_d35f8e895a` | 2021 | 图书馆短视频传播及互动效果影响因素模型及实证分析——基于“上瘾模型”的探索 | 图书情报工作 | 213 | 7270 | yes | yes | skimmed |
| 3 | 76.4 | `cnki_2020_5ca581e54f` | 2020 | 公共图书馆短视频公众平台建设现状分析 | 图书馆学研究 | 107 | 1954 | no | no | metadata-only |

## 后续候选池

| Rank | Score | Citekey | Year | Title | Source | Cited | Downloads | Reader | PDF | Read status |
|---:|---:|---|---:|---|---|---:|---:|---|---|---|
| 1 | 80.2 | `cnki_2021_5530e86157` | 2021 | 基于短视频营销的公共图书馆数字阅读推广策略研究 | 图书馆工作与研究 | 99 | 2915 | yes | yes | metadata-only |
| 2 | 80.0 | `cnki_2021_3771e58987` | 2021 | 公共图书馆和高校图书馆短视频营销比较研究 | 大学图书馆学报 | 92 | 3214 | no | no | metadata-only |
| 3 | 79.5 | `cnki_2021_d35f8e895a` | 2021 | 图书馆短视频传播及互动效果影响因素模型及实证分析——基于“上瘾模型”的探索 | 图书情报工作 | 213 | 7270 | yes | yes | skimmed |
| 4 | 76.4 | `cnki_2020_5ca581e54f` | 2020 | 公共图书馆短视频公众平台建设现状分析 | 图书馆学研究 | 107 | 1954 | no | no | metadata-only |
| 5 | 75.9 | `cnki_2019_94a1721837` | 2019 | 短视频APP在图书馆推广中的应用及发展策略——基于平台数据的统计分析 | 图书馆学研究 | 130 | 2989 | no | no | metadata-only |
| 6 | 75.3 | `cnki_2021_2ba9195a8a` | 2021 | 我国省级公共图书馆短视频服务运营探析——基于抖音App的数据分析 | 图书馆学研究 | 79 | 2025 | no | no | metadata-only |
| 7 | 74.0 | `cnki_2023_34348faa1e` | 2023 | 基于SICAS模型的公共图书馆短视频营销策略研究 | 图书馆工作与研究 | 105 | 5245 | yes | yes | metadata-only |
| 8 | 72.7 | `cnki_2021_645f03f388` | 2021 | 图书馆短视频账号传播力研究——以省级公共图书馆为例 | 图书馆学研究 | 74 | 2082 | no | no | metadata-only |
| 9 | 72.0 | `cnki_2021_2bcdca1cf9` | 2021 | 短视频社会化阅读推广效果分析——以抖音短视频为例 | 图书馆 | 74 | 4127 | no | no | metadata-only |
| 10 | 71.7 | `cnki_2020_62aa02b5b0` | 2020 | 大学生手机短视频过度使用行为影响因素研究 | 图书馆学研究 | 167 | 13278 | no | no | metadata-only |
| 11 | 63.9 | `cnki_2022_efd2209e07` | 2022 | 基于4P营销模型的高校图书馆读书类短视频运营策略研究 | 图书馆工作与研究 | 72 | 4461 | no | no | metadata-only |
| 12 | 62.8 | `cnki_2019_d713007c64` | 2019 | 媒体融合背景下高校图书馆服务营销策略研究 | 图书馆工作与研究 | 109 | 2415 | no | no | metadata-only |

## 今日记录动作

- [ ] 读完后，把真实阅读状态只升级到实际达到的层级：`skimmed`、`human-read` 或 `verified`。
- [ ] 把主读论文的创新点、局限性和可转化机会写入 `projects/<project>/literature/innovation_limitation_bank.md`。
- [ ] 若讨论形成稳定判断，更新 `projects/<project>/03_literature_synthesis.md`。
- [ ] 若用于论文主张，补 source locator，再运行 `make evidence-gate PROJECT=<project>`。
