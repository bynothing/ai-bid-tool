# Generated Baselines

本目录用于保存当前系统生成结果的基线快照。

每个基线建议使用独立目录：

```text
generated-baselines/
  YYYYMMDD-target-process-interaction/
    job.json
    manifest.json
    output.png
    output.svg
    review.md
```

规则：

- 基线不是最终成品，而是差距分析依据。
- 每个基线必须能追溯到 job 和 renderer。
- 如果基线成为长期回归样本，应迁移或复制到 `tests/fixtures/illustration_cases/`。

## 当前基线

| 基线 | 说明 | 评分/记录 |
| --- | --- | --- |
| `iteration-001-process-interaction/` | A 类工艺流程 / 系统交互大图，输出 `.drawio`、SVG、PNG 和 manifest | `../reviews/baseline-process-interaction-iteration-001.md` |
| `iteration-002-layered-explainer/` | D 类多层能力说明图，参考“AI 系统七层架构全景图” | `../reviews/baseline-layered-explainer-iteration-002.md` |
