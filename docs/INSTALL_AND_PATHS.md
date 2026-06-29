# 软件安装与路径

当前脚本会自动检测：

- Python: `python3`
- R: `Rscript`
- MATLAB: `matlab`
- Pandoc: `pandoc`
- LaTeX PDF 编译器: `tectonic`
- Gephi: `gephi`

推荐使用 Anaconda Python 运行工作流：

```bash
/Users/leung/anaconda3/bin/python scripts/check_environment.py
```

也可以直接运行：

```bash
python3 scripts/check_environment.py
```

本机当前已检测到 Anaconda Python、Rscript、Pandoc 和 Gephi。Gephi 是 macOS app 安装，路径已记录在 `config/software_paths.yaml`；MATLAB、Tectonic 没有在 PATH 里找到，如果已经安装，可在同一个配置文件里手动填路径。

推荐补装：

- Zotero: 管理正式文献库和 BibTeX 导出。
- Better BibTeX for Zotero: 生成稳定 citekey。
- Tectonic 或 MacTeX: 从 LaTeX 编译正式 PDF。
- Gephi: 做共词、共引、作者合作等网络图。
