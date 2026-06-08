# Pipeline Map

`pipeline/` 承载标书自动化的阶段编排和各阶段实现。

## 阶段

| 阶段 | 文件 | 职责 |
| --- | --- | --- |
| S1 | `stages/s1_parse.py` | 招标文件解析，提取关键信息、评分、风险、技术需求 |
| S2 | `stages/s2_outline.py` | 章节大纲设计 |
| S3 | `stages/s3_body.py` | 正文撰写 |
| S4 | gate / 状态 | 人工确认和内容冻结 |
| S5_tables | `stages/s5_tables.py` | 表格内容规划 |
| S5 | `stages/s5_illustrate.py` | 配图任务规划 |
| S6 | `stages/s6_synthesize.py` | 表格 + 配图 + 正文合成 |
| S7 | `stages/s7_verify.py` | 需求响应闭环校验 |
| S8 | `stages/s8_export.py` | 导出 |
| S9 | `stages/s9_deviation.py` | 偏离表 |

## 支撑模块

| 文件 | 职责 |
| --- | --- |
| `engine.py` | 阶段编排 |
| `validator.py` | 阶段输出校验 |
| `trace.py` | 需求追踪 |
| `chapter_planner.py` | 章节规划辅助 |
| `style_check.py` | 样式检查 |

## 修改规则

- 阶段输出结构变化时，同步更新 `src/bid_tool/schemas/` 和测试。
- Prompt 变化时，同步检查 `src/bid_tool/prompts/`。
- 用户可见流程变化时，同步更新 `README.md` 和 `CHANGELOG.md`。
- 与配图相关变化要同步查看 `docs/quality-targets/illustration/`。
