# 《图书情报工作》期刊 Profile

Target journal: 《图书情报工作》  
Journal site: https://www.lis.ac.cn/CN/0252-3116/home.shtml  
Submission system: https://tsqbgzauthor.manuscriptcloud.com  
Data submission entry: https://www.homest.org.cn/openjournal/index

This profile adapts the local workflow to a Chinese information resource
management journal context. Check the official pages before final submission,
because journal policies can change.

## Positioning

Use this profile when the target venue is 《图书情报工作》 or when a Chinese
library/information science paper should follow a similar structure.

The journal focuses on information resource management and related fields,
especially research on data resource management and services, knowledge
management and services, information/intelligence services, and intelligent
services in digital, networked, and open-science environments.

Recognized article orientations include:

- 专题研究
- 理论研究
- 工作研究
- 情报研究
- 知识组织
- 综述述评
- 海外观察

## 2026 Topic Fit Signals

Before creating a formal project, check whether the idea matches at least one
of these current fit signals:

- 信息资源管理自主知识体系
- 新质生产力与图书情报事业高质量发展
- AI 赋能的信息资源管理范式变革
- “十五五”战略规划相关议题
- 数据要素、公共数据、数据可信空间、数据资源开发与利用
- LLM 驱动的智慧图书馆、知识服务、智能服务
- 数字学术服务、情报保障、智库建设
- 图情档场景下的智能机器人应用评估

Do not force-fit. A paper still needs a clear research question, evidence, and
field contribution.

## Manuscript Structure

Default manuscript files should follow Chinese-first structure:

1. 中文题目
2. 作者、单位、城市、邮编
3. 中文结构化摘要
4. 中文关键词，3-8 个
5. 中图分类号，按《中国图书馆分类法》四级或五级类目
6. 正文：引言、理论/文献、方法/过程、结果、讨论、结论
7. 基金项目脚注，最多两个项目
8. 作者简介，提供第一作者或通信作者 E-mail
9. 表、图、地图说明，均需中英文题名
10. 参考文献，按 GB/T 7714-2015，并为中文文献补充英文翻译信息
11. 作者贡献说明
12. 英文题目、作者拼音、单位英文信息
13. Long English abstract, 400-800 English words
14. English keywords

## Abstract Contract

Chinese abstract:

- `[目的/意义]`: Why this paper matters and what problem it addresses.
- `[方法/过程]`: Research process, data, tools, methods, or reasoning path.
- `[结果/结论]`: Objective findings, conclusions, practical value, reliability,
  innovation, and limitations where relevant.

English abstract:

- `[Purpose/Significance]`
- `[Method/Process]`
- `[Result/Conclusion]`
- `[Innovation/Value]`
- `[Insufficient/Improvement]`

The English abstract should not be a literal short translation. It should be a
long, coherent account of the Chinese paper's purpose, method, findings,
contribution, and limitations.

## Figures, Tables, And Maps

- Tables should normally be three-line tables; no blank table headers.
- Figures must have readable text, clear labels, and publication-grade resolution.
- The official template states figure text should be clear, with a 7 pt text
  reference, and a double-column maximum width of 8 cm.
- Figure resolution should be at least 300 dpi/ppi.
- Every figure and table title should have a Chinese title and an English title.
- If a manuscript includes maps, use approved standard-map basemaps and do not
  alter the basemap improperly. Map materials require special compliance review.

Local workflow rule: every final figure still needs a `figures/specs/*.md`
contract with claim, evidence chain, source data, script, export, and QA.

## References

- Use GB/T 7714-2015 style.
- Chinese references need corresponding English information in parentheses or
  journal-required bilingual form.
- If a reference has more than three authors, retain the first three and use
  `等` or `et al.` as appropriate.
- Foreign references and translated Chinese-reference author names should use
  surname plus initials, with names in uppercase.
- Data sets can be cited as data references when related data are deposited.

## Data Policy

The journal encourages sharing data that directly support paper conclusions.

Project workflow implications:

- Add a data availability statement before submission.
- If data can be shared, prefer a public repository and record DOI/CSTR or a
  stable URL.
- ScienceDB is listed by the journal as a recommended repository.
- If data are unsuitable for sharing, record the reason, such as ethics,
  privacy, confidentiality, third-party rights, or no new data generated.
- If the study produces data, code, algorithm, model, protocol, or materials
  that support the conclusions, include them in the integrity gate.

## AI Policy

Workflow rule for this journal:

- Do not list AI tools as authors.
- Do not cite AI as an author.
- If AI tools are used for data collection/analysis, figure elements, code,
  algorithms, text generation, or language polishing, disclose the tool, usage
  process, role, and contribution in the data source, method design, or
  conclusion section as appropriate.
- Major AI-generated manuscript content without proper disclosure is treated as
  a serious integrity risk.

Local rule: keep `manuscript/ai_usage_disclosure.md` or record disclosure in
`08_publication_readiness.md` before submission.

## Authorship And Ethics

- The first author is the main contributor to academic idea, research content,
  initial drafting, and revision.
- A corresponding author can be set when needed.
- The journal states it does not use co-first-author or co-corresponding-author
  designations.
- Publication ethics and academic integrity checks should run before submission.

## Local Workflow Changes

When this profile is active:

- Use Chinese filenames and Chinese manuscript sections where useful, but keep
  stable ASCII project slugs.
- Treat Chinese literature as first-class evidence, not only English sources.
- Add CNKI/万方/维普/manual source fields when importing literature manually.
- For each key Chinese source, record whether the user has actually read the
  full text.
- Before writing, classify the paper as 理论研究 / 工作研究 / 情报研究 / 知识组织 / 综述述评 / 海外观察 / 专题研究.
- Before submission, run the `图书情报工作` checklist in
  `manuscript/submission_checklist_tushuqingbaogongzuo.md`.
- For old projects, run `make backfill PROJECT=<slug> APPLY=1` once to add
  missing target-journal, data-governance, AI-disclosure, and production files
  without overwriting existing drafts.
- Before internal pre-review, run `make citation-audit PROJECT=<slug>` to create
  `manuscript/citation_audit_gbt7714.md`.
- Before final submission preparation, run `make submission-package
  PROJECT=<slug>` to build a local submission package. The package intentionally
  excludes raw data.

## Official Sources Checked

- Home page: https://www.lis.ac.cn/CN/0252-3116/home.shtml
- 选题指南: https://www.lis.ac.cn/CN/column/column22.shtml
- 目标和范围: https://www.lis.ac.cn/CN/column/column32.shtml
- 论文写作模板: https://www.lis.ac.cn/CN/column/column41.shtml
- 编辑出版流程: https://www.lis.ac.cn/CN/column/column24.shtml
- 作者署名规定: https://www.lis.ac.cn/CN/column/column46.shtml
- 数据共享政策: https://www.lis.ac.cn/CN/column/column38.shtml
- AI政策声明: https://www.lis.ac.cn/CN/column/column27.shtml
