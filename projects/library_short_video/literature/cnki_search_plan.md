# CNKI Search Plan - 图书馆短视频相关研究

Date: 2026-06-20
Project: `library_short_video`

## Goal

Use CNKI metadata and legally obtained full texts to select 5-7 relevant papers on library short-video research for learning and discussion. The first output should be a metadata-level frontier radar. After authorized PDFs are available, selected papers can be upgraded to source-grounded readers.

## Access Boundary

- The user logs in to CNKI through their own browser, institution VPN, or library portal.
- Codex must not receive passwords or bypass CAPTCHA, paywalls, download limits, or access controls.
- CNKI abstracts and metadata are treated as `metadata-only` until the user reads/validates full text.

## Core Search Queries

Use CNKI advanced search. Prefer `主题` first; if too many irrelevant results, switch to `篇名`.

### Query A: Core Topic

```text
主题 = 图书馆 AND 主题 = 短视频
```

### Query B: University Libraries

```text
主题 = 高校图书馆 AND 主题 = 短视频
```

### Query C: Public Libraries

```text
主题 = 公共图书馆 AND 主题 = 短视频
```

### Query D: Reading Promotion

```text
主题 = 阅读推广 AND 主题 = 短视频
```

### Query E: Platform-Specific Expansion

```text
主题 = 图书馆 AND (主题 = 抖音 OR 主题 = 快手 OR 主题 = 视频号 OR 主题 = B站 OR 主题 = 哔哩哔哩)
```

### Query F: Broader New-Media Boundary

Use only if A-E return too few high-quality records.

```text
主题 = 图书馆 AND (主题 = 新媒体 OR 主题 = 融媒体 OR 主题 = 社交媒体) AND (主题 = 视频 OR 主题 = 短视频)
```

## Recommended Filters

- Time range: 2019-2026 first. If too few results, extend to 2016-2026.
- Literature type: journal articles first; optionally include dissertations and conference papers as background.
- Disciplines: library and information science / information resource management / journalism and communication if CNKI categories are available.
- Sort twice and export both if possible:
  - newest first for frontier radar
  - citation/download count for influence

## Export Requirements

Export metadata to:

```text
library/cnki_exports/library_short_video/
```

Preferred formats:

1. `.xlsx`
2. `.csv`
3. RIS or EndNote text

Fields to include when CNKI allows field selection:

- title
- authors
- author affiliation
- source/journal
- year
- issue
- abstract
- keywords
- DOI
- fund
- citation count
- download count
- URL or CNKI identifier

Recommended filenames:

```text
library_short_video_core_2019_2026.xlsx
library_short_video_platform_2019_2026.xlsx
library_short_video_reading_promotion_2019_2026.xlsx
```

## Import Commands

Dry-run first:

```bash
make import-cnki INPUT=library/cnki_exports/library_short_video/<file> TAG=library_short_video DRY=1
```

Then import:

```bash
make import-cnki INPUT=library/cnki_exports/library_short_video/<file> TAG=library_short_video
```

Generate 5-7 paper frontier radar:

```bash
make cnki-frontier TAG=library_short_video TOPIC="图书馆短视频相关研究" LIMIT=7 SINCE=2019
```

Create one-paper discussion card:

```bash
make paper-brief CITEKEY=<citekey>
```

Upgrade to full reader after legal PDF access:

```bash
make paper-reader PROJECT=library_short_video CITEKEY=<citekey> PDF=library/pdfs/library_short_video/<paper>.pdf
make evidence-gate PROJECT=library_short_video
```

## Selection Criteria For 5-7 Papers

Select papers with a balanced mix:

1. Directly about `图书馆 + 短视频`.
2. At least one university-library case.
3. At least one public-library or public-cultural-service case if available.
4. At least one reading-promotion / user-service / knowledge-service angle.
5. At least one platform-operation angle such as Douyin, WeChat Channels, Bilibili, or Kuaishou.
6. Prefer recent papers, but keep one older or highly cited paper if it shaped the discussion.
7. Mark every selected paper as `metadata-only` until full text is obtained and read.

## Learning Questions

For each selected paper, answer:

1. What library problem does short video solve or claim to solve?
2. Is the paper mainly conceptual, case-based, survey-based, platform-data-based, or empirical?
3. What does it count as "effectiveness": views, likes, interaction, reading promotion, user satisfaction, service reach, or knowledge dissemination?
4. What is the actual evidence, and what remains speculative?
5. What can be borrowed for a Chinese LIS paper targeting 《图书情报工作》?

