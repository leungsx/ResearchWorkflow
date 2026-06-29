# Obsidian 知识图谱与方向链

这个模块把 Obsidian 的 `[[双链]]` 导出成 Gephi 可读的 nodes/edges，用于观察你的知识结构、研究方向和潜在灵感。

## 方向链

建议每个重要知识点都尽量连接成方向链：

```text
问题/灵感 -> 概念 -> 方法 -> 文献 -> 数据/实验 -> 结果 -> 论文主张 -> 新问题
```

例子：

```text
AI辅助科研 -> 人机协作 -> Socratic questioning -> 文献矩阵 -> Idea Lab -> 研究问题质量
```

## 导出图谱

```bash
make obsidian-graph
```

输出：

- `vault/13_Knowledge_Graph/obsidian_nodes.csv`
- `vault/13_Knowledge_Graph/obsidian_edges.csv`

## 浏览器图谱入口

```bash
make learning-dashboard
```

必须刷新：

- `knowledge_graph/index.html`

这个页面是用户默认查看图谱的入口，应以可视化关系图为主体，至少支持：

- 搜索节点。
- 按文献、概念、方法、项目等类型筛选。
- 点击节点查看相邻节点和连接数。
- 保留 CSV 链接作为源数据核对入口，但不把表格作为主界面。

可导入 Gephi：

1. 导入 `obsidian_nodes.csv` 作为 Nodes table。
2. 导入 `obsidian_edges.csv` 作为 Edges table。
3. 用 Type 字段区分 concept、method、literature、project、idea、learning。

## Codex 如何利用知识图谱

当你问“我还能做什么研究”时，Codex 应该查看：

- 哪些概念连接最多。
- 哪些方法还没有连接到项目。
- 哪些 idea cards 缺少文献或方法支撑。
- 哪些文献集群没有转成实验或论文主张。
- 哪些知识点经常复习但还未掌握。

这些都可以变成新的研究问题或学习任务。
