# Schemas Map

本目录存放阶段输出、配图任务和渲染输入相关 JSON Schema。

## 规则

- Schema 是阶段之间、AI 输出和工具执行之间的契约。
- 修改字段名、字段类型、必填项时，必须更新测试。
- 用户可见协议变化时，必须更新 `CHANGELOG.md`。
- 配图 Job 变化时，检查 `src/bid_tool/schemas/AI_ILLUSTRATION_API_V2.md`。

## 常用文件

| 文件 | 作用 |
| --- | --- |
| `illustration_job_v2.schema.json` | Illustration Job v2 |
| `AI_ILLUSTRATION_API_V2.md` | AI 配图调用说明 |
| `s5_table_plan.schema.json` | 表格规划 |
| `s7_trace_matrix.schema.json` | 响应闭环矩阵 |
| `svg_diagram.schema.json` | SVG 图输入 |
| `echarts_diagram.schema.json` | ECharts 图输入 |

## 验证

```powershell
python -m pytest tests/test_schemas.py
```
