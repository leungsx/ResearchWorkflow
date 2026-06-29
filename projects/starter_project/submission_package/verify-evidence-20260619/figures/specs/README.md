# Figure Specs

Create one Markdown spec per final figure, for example `fig1_main_result.md`.
Do this before generating or polishing publication figures.

## Figure Contract Template

```markdown
# Figure ID

## Core Conclusion

One sentence the figure must defend:

## Evidence Chain

| Panel | Evidence role | Data source | Script / command | Statistical note | Risk |
|---|---|---|---|---|---|
| A |  |  |  |  |  |

## Figure Archetype

- quantitative grid / schematic-led composite / image plate + quant / asymmetric mixed-modality figure

## Backend

- Python / R
- Runtime and packages checked:
- Reason for backend choice:

## Journal / Export Contract

- Target venue:
- Final size:
- Required formats: SVG / PDF / TIFF / PNG
- Editable text required: yes / no
- Source data file:
- Image-integrity notes:

## Legend Notes

- Sample size / replicate unit:
- Error bars:
- Statistical test:
- Multiple-comparison handling:
- Data exclusions:

## QA

- [ ] Axes, units, legends, labels are readable.
- [ ] Colors are consistent across panels.
- [ ] Figure can be regenerated from data and script.
- [ ] Export files exist in `figures/final/`.
- [ ] Claim does not exceed the evidence.
```
