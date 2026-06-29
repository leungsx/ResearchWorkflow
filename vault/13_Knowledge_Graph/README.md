# Knowledge Graph

这里保存知识索引和 Obsidian 双链导出的 Gephi 数据。

## 在每日精读中的职责

每篇新精读论文都应该带来一组明确关系：

- 论文 -> 概念
- 论文 -> 方法
- 论文 -> 项目
- 概念 -> 方法
- 局限/机会 -> Idea Lab 或研究问题

这些关系优先通过 Obsidian `[[双链]]` 写入论文笔记、概念卡和方法卡，再导出为 CSV。

常用命令：

```bash
make obsidian-graph
make learning-dashboard
```

可视化入口：

```text
knowledge_graph/index.html
study_dashboard.html
```
