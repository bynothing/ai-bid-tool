# 本地 ECharts 运行依赖

本目录用于承载 `echarts-workbench/index.html` 离线运行所需的浏览器脚本。

| 文件 | 用途 | 来源 |
| --- | --- | --- |
| `echarts.min.js` | 本地 HTML 图表渲染与导出 | Apache ECharts `5.6.0`，复用当前前端工程已安装的 `echarts5/dist/echarts.min.js` |
| `LICENSE.echarts.txt` | 第三方许可证 | Apache ECharts 包内 `LICENSE` |

当前工作台不访问 CDN，双击打开 `index.html` 即可使用。升级 ECharts 时需要同步替换上述两个文件，并重新执行柱线图、雷达图和 Sankey 图的导出验证。

参考链接：https://echarts.apache.org/
