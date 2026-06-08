# Illustration V2 Source Map

`illustration_v2` 是当前配图执行环境主线。

## 目标

将结构化 Illustration Job 稳定转化为可审查、可导出、可装配的 SVG/PNG/Draw.io 资产。

## 目录

| 路径 | 职责 |
| --- | --- |
| `api.py` | Python API：load、validate、plan、render |
| `toolkit.py` | `bid-illustrate` CLI |
| `standalone.py` | 独立工具包构建 |
| `core/` | Job 模型、能力目录、决策、校验、manifest、文本测量 |
| `renderers/` | Draw.io、template_svg、组件库 |
| `templates/` | 模板契约、模板说明、SVG 模板 |
| `catalogs/` | 能力目录 |
| `examples/` | 包内示例 Job |
| `materials/` | 参考素材和分析 |

## 当前短板

- 工程级质量不足。
- 箭头和复杂关系表达需要治理。
- 决策层 tier/fallback 记录需要加强。
- 几何/关系 QA 需要补齐。

## 相关文档

- `docs/architecture/illustration-v2/current-architecture.md`
- `docs/architecture/illustration-v2/decision-analysis.md`
- `docs/quality-targets/illustration/README.md`
- `docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md`
- `docs/standards/illustration/drawing-content-standard.md`
