# ECharts 本地数据图工作台

该页面用于在编写标书时快速审阅和导出 AI 生成的数据型图件，直接在浏览器本地运行，不需要服务端和网络。

## 打开方式

双击打开 [index.html](<index.html>)，或在 PowerShell 执行：

```powershell
Start-Process '.\web\echarts-workbench\index.html'
```

工作台内置三张演示图：

| 图型 | 适合内容 | 当前支持 |
| --- | --- | --- |
| 柱线组合图 | 规模与覆盖率、数量与比例、趋势对比 | `bar_line` |
| 雷达图 | 能力响应、技术评分、维度比较 | `radar` |
| Sankey 流向图 | 数据来源、汇聚过程、应用去向 | `sankey` |

## AI 生成与使用流程

1. 让大模型按 [echarts_diagram.schema.json](<../../schema/echarts_diagram.schema.json>) 输出 JSON。
2. 在工作台选择“导入 JSON”，打开描述文件进行审图。
3. 选择单张图，导出 SVG 用于正式文档；导出 PNG 用于沟通预览。
4. 对模拟数据、推断内容或待确认口径，必须在 `note`、`source`、`dataNotice` 中明确标注。

可直接参考的输入文件：[示例_ECharts数据图描述.json](<../../examples/示例_ECharts数据图描述.json>)。

## 设计约定

- 页面和导出图均为清晰白底、深色正文、高对比连线的标书样式。
- AI 提供语义化图表描述和数据，不直接输出 JavaScript 或任意 ECharts `option`。
- `vendor/echarts.min.js` 为本地 ECharts 运行依赖，来源与许可证记录在 [vendor/README.md](<vendor/README.md>)。
