# 数据与科研图规则

## 数据目录

- `data/raw`: 原始数据，只读保存。
- `data/interim`: 中间数据，可以重建。
- `data/processed`: 用于统计、建模和绘图的清洗数据。

## 图表目录

- `figures/raw`: 初步探索图。
- `figures/final`: 可用于论文和汇报的最终图。
- `figures/specs`: 每张最终图的图件合同和图表说明。

## 正式图件合同

生成或润色 `figures/final` 中的图之前，先在 `figures/specs/<figure_id>.md`
写清楚：

- 核心结论：这张图必须支撑的一句话。
- 证据链：每个 panel 对应的数据、脚本、统计方法和风险。
- 图件类型：quantitative grid、schematic-led composite、image plate + quant 或 mixed-modality。
- 绘图后端：Python 或 R；选定后不混用另一个后端做预览或替代渲染。
- 导出合同：目标期刊/汇报场景、尺寸、SVG/PDF/TIFF/PNG、可编辑文字、source data。
- 完整性说明：样本量、重复单位、误差线、统计检验、排除标准和图像处理边界。

## 合格科研图最低标准

- 图号、标题、变量含义清楚。
- 坐标轴有名称和单位。
- 图例、颜色、分组含义明确。
- 字体、线宽、分辨率适合印刷。
- 图注说明数据来源、样本量和统计方法。
- 能从脚本和数据完全复现。
- 图的结论不能超过数据和统计结果能支持的范围。
