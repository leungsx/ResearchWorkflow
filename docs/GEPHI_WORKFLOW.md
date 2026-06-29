# Gephi 网络图工作流

本工作流用 `library/relations.csv` 作为统一关系表，再导出 Gephi 可导入的 `nodes.csv` 和 `edges.csv`。

## 1. 维护关系表

编辑：

```text
library/relations.csv
```

字段含义：

- `source`: 起点，可以是作者、论文 citekey、概念、方法或关键词。
- `target`: 终点。
- `relation`: 关系类型，例如 `cites`、`co_occurs`、`uses_method`、`supports_claim`。
- `weight`: 权重，默认 1。
- `evidence`: 证据来源，例如文献 citekey、页码、笔记路径或数据文件。

## 2. 导出 Gephi 文件

```bash
cd /Users/leung/ResearchWorkflow
make gephi
```

输出：

```text
library/gephi/nodes.csv
library/gephi/edges.csv
```

## 3. 导入 Gephi

1. 打开 Gephi。
2. `File -> Import Spreadsheet`。
3. 先导入 `nodes.csv`，类型选择 `Nodes table`。
4. 再导入 `edges.csv`，类型选择 `Edges table`。
5. 在 Overview 中选择布局算法，例如 ForceAtlas2、Fruchterman Reingold 或 Yifan Hu。
6. 用 `Label`、`Relation`、`Weight` 做颜色、粗细和标签映射。

## 4. 常见科研图类型

- 概念共现网络：`source/target` 为关键词或概念。
- 文献引用网络：`source/target` 为 citekey，`relation=cites`。
- 方法-论文二分网络：一端是方法，一端是论文。
- 作者合作网络：`source/target` 为作者名，`relation=coauthor`。
- 论断-证据网络：一端是论文主张，一端是文献或实验结果。

## 5. 归档要求

最终用于论文或汇报的网络图，需要保存：

- Gephi project: `projects/<slug>/figures/raw/*.gephi`
- 导出图片: `projects/<slug>/figures/final/`
- 图表说明: `projects/<slug>/figures/specs/`
- 数据来源: `library/relations.csv` 或项目内关系表

