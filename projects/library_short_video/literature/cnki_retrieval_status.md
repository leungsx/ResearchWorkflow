# CNKI Retrieval Status - Library Short Video

Updated: 2026-06-22

## Scope

- Topic: 图书馆短视频相关研究
- CNKI query used: `主题：图书馆 * 短视频`
- Date range: `2019-01-01` to `2026-06-20`
- Access boundary: files were downloaded through the user's authorized CNKI/Chrome/VPN session. No password, CAPTCHA bypass, or paywall bypass was used.

## Current Learning Set

| Citekey | Title | Local original | Reader | Discussion card | Notes |
|---|---|---|---|---|---|
| `cnki_2021_d35f8e895a` | 图书馆短视频传播及互动效果影响因素模型及实证分析——基于“上瘾模型”的探索 | `library/pdfs/library_short_video/cnki_2021_d35f8e895a.caj` | `literature/readers/cnki_2021_d35f8e895a/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2021_d35f8e895a.md` | 真 CAJ；reader 来自授权浏览器 HTML 文本抽取；另已转为 `library/pdfs/library_short_video/converted/cnki_2021_d35f8e895a.pdf`，未覆盖已写好的精读笔记。 |
| `cnki_2021_dfab60236e` | 抖音阅读推广短视频传播效果影响因素研究 | `library/pdfs/library_short_video/cnki_2021_dfab60236e.caj` | `literature/readers/cnki_2021_dfab60236e/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2021_dfab60236e.md` | 真 CAJ；已转为 `library/pdfs/library_short_video/converted/cnki_2021_dfab60236e.pdf` 并用 PDF 重建 reader，23 blocks。 |
| `cnki_2020_64b4f881c9` | 图书馆短视频发展现状、问题与对策分析——以抖音平台为例 | `library/pdfs/library_short_video/cnki_2020_64b4f881c9.caj` | `literature/readers/cnki_2020_64b4f881c9/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2020_64b4f881c9.md` | 真 CAJ；已用本地 `caj2pdf` 转为 `library/pdfs/library_short_video/converted/cnki_2020_64b4f881c9.pdf`；报告见 `literature/caj_conversion/cnki_2020_64b4f881c9.md`。 |
| `cnki_2020_2a150c6df8` | 图书馆热门短视频内容规律探究——基于抖音平台的实证研究 | `library/pdfs/library_short_video/cnki_2020_2a150c6df8.caj` | `literature/readers/cnki_2020_2a150c6df8/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2020_2a150c6df8.md` | 文件扩展名为 `.caj`，但内容是可抽取 PDF。 |
| `cnki_2021_7556aafa99` | 公共图书馆“抖音”短视频服务现状及发展策略研究 | `library/pdfs/library_short_video/cnki_2021_7556aafa99.caj` | `literature/readers/cnki_2021_7556aafa99/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2021_7556aafa99.md` | 文件扩展名为 `.caj`，但内容是可抽取 PDF。 |
| `cnki_2023_34348faa1e` | 基于SICAS模型的公共图书馆短视频营销策略研究 | `library/pdfs/library_short_video/cnki_2023_34348faa1e.caj` | `literature/readers/cnki_2023_34348faa1e/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2023_34348faa1e.md` | 真 CAJ；已用本地 `caj2pdf` 转为 `library/pdfs/library_short_video/converted/cnki_2023_34348faa1e.pdf`；报告见 `literature/caj_conversion/cnki_2023_34348faa1e.md`。 |
| `cnki_2021_5530e86157` | 基于短视频营销的公共图书馆数字阅读推广策略研究 | `library/pdfs/library_short_video/cnki_2021_5530e86157.caj` | `literature/readers/cnki_2021_5530e86157/paper.md` | `vault/15_CNKI_Frontier/paper_briefs/cnki_2021_5530e86157.md` | 文件扩展名为 `.caj`，但内容是可抽取 PDF。 |

## Current Completion

- CNKI metadata pool: 60 project-tagged rows in `library/literature_matrix.csv`.
- Authorized local full texts recorded in matrix: 8 / 60.
- Discussion cards: 7 / 8 for the current local learning set.
- Reader packages: 8 / 8.
- Reader gaps: none for the current learning set.
- CAJ conversion route: local `make caj-convert` workflow using MuPDF `mutool` and `tools/caj2pdf/caj2pdf` is available and verified on the two true CAJ reader gaps.

## 2026-06-22 Run Notes

- Generated today's recommendation library entry:
  `vault/15_CNKI_Frontier/daily_recommendations/2026-06-22-library_short_video.md`.
- Recommendation state updated:
  `projects/library_short_video/literature/daily_learning_state.json`.
- Today's primary recommendation is `cnki_2019_94a1721837`
  “短视频APP在图书馆推广中的应用及发展策略——基于平台数据的统计分析”.
- Chrome browser automation was blocked because the Codex Chrome Extension is
  not installed/enabled in the selected Chrome profile. No CNKI paywall,
  CAPTCHA, or download limit was bypassed.
- After the extension was enabled, Chrome opened normally, but CNKI navigation
  was blocked by Chrome's privacy interstitial:
  `net::ERR_CERT_COMMON_NAME_INVALID` for `https://www.cnki.net/` and the CNKI
  detail pages. Codex did not bypass the browser safety warning.
- A second attempt followed the slower user-facing route
  `CNKI main page -> Advanced Search -> enter topic/date range -> open detail
  page -> PDF下载`, but Chrome still blocked the official entry points before
  the search form could load. Tested URLs included `http://www.cnki.net/`
  (redirects to HTTPS), `https://www.cnki.net/`,
  `https://kns.cnki.net/kns8s/AdvSearch`,
  `https://kns.cnki.net/kns8/AdvSearch`, and `https://kns.cnki.net/`.
  All returned `net::ERR_CERT_COMMON_NAME_INVALID`.
- Fixed `scripts/cnki_click_download_titles.py` so existing `.caj` files no
  longer cause the detail-page PDF route to be skipped. It now skips only when
  an existing PDF is present for PDF-oriented modes, and it filters CNKI ad or
  recommendation PDFs before clicking `PDF下载`.

## Notes For Future Sessions

- Future CNKI full-text downloads should prefer the detail-page PDF route: click paper title from the result list, open the paper detail/abstract page, then click `PDF下载`. The result-list download button is only the fallback because it often returns `.caj`.
- `scripts/cnki_click_download_titles.py` now defaults to `--download-mode detail-pdf-first`: detail-page PDF first, result-list direct download second, CAJ conversion third.
- For PDF-only catch-up after Chrome access is restored, use
  `make cnki-download PROJECT=library_short_video TITLES=<titles.txt> MODE=detail-pdf-only`
  or the batch route
  `/Users/leung/anaconda3/bin/python scripts/cnki_batch_pdf_download.py --metadata-json library/cnki_exports/library_short_video/cnki_library_short_video_2026-06-21_top60.json --project library_short_video --target-total 60 --update-matrix`.
- CNKI may show a Save dialog after each download click. The user can click `保存`; Codex then checks `Downloads`, copies the file to `library/pdfs/library_short_video/`, normalizes the filename to `<citekey>.<ext>`, and updates `library/literature_matrix.csv`.
- If the downloaded file is a true CAJ/KDH file, run `make caj-convert PROJECT=library_short_video CITEKEY=<citekey> UPDATE=1 RUN_READER=1`. This writes a converted PDF under `library/pdfs/library_short_video/converted/`, a conversion report under `projects/library_short_video/literature/caj_conversion/`, and a reader package under `projects/library_short_video/literature/readers/`.
- The earlier frontier radar is an algorithmic metadata-level selection. The current learning set is the actually downloaded and organized set from the authorized CNKI result page.
- Do not mark any paper as `human-read` or `verified` until the user actually reads it or Codex completes a source-grounded reading session with explicit user confirmation.
