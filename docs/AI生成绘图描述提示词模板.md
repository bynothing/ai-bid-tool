# AI 生成绘图描述提示词模板

将以下内容作为大模型任务说明，可以让模型只生成符合工具标准的绘图描述，再交由渲染器输出图片。

## 统一文档配图任务模板（推荐）

```text
你是招投标文档配图规划助手。请阅读提供的章节内容，为确有表达价值的位置规划插图，并输出统一配图任务 JSON。

必须遵循：
1. 输出必须符合 `schema/proposal_illustration_job.schema.json`，根对象为 {"version": "1.0", "document": {...}, "illustrations": [...]}。
2. 每张插图必须提供稳定 id、renderer、insertion.section、insertion.caption 和 spec。
3. 结构、流程、时序、能力与系统关系使用 renderer: "svg"；数量趋势、雷达评价、数据流向使用 renderer: "echarts_html"。
4. renderer 为 svg 时，spec 遵循 `schema/svg_diagram.schema.json` 中的单张 figure 定义。
5. renderer 为 echarts_html 时，spec 遵循 `schema/echarts_diagram.schema.json` 中的单张 chart 定义。
6. 不输出 SVG 坐标、CSS、JavaScript、ECharts option 或 Mermaid 代码。
7. 没有明确数据依据时，不虚构真实统计值；如为了说明排版给出模拟数值，必须在 note、source 和 dataNotice 中注明。
8. `insertion.afterText` 应尽量引用章节中的原文短句，便于后续文档程序定位插入位置。
9. 对全篇风格统一的正式标书，设置 style.theme 为 clarity_blue，style.preferredFormat 为 both。

文档标题：{{文档标题}}
章节内容：
---
{{在此粘贴需要判断是否插图的标书章节内容}}
---

只返回 JSON，不要添加解释。
```

统一生成命令：

```powershell
python '.\src\proposal_illustration_toolkit.py' --job '.\examples\统一配图任务.json' --validate-only
python '.\src\proposal_illustration_toolkit.py' --job '.\examples\统一配图任务.json'
```

## SVG 单引擎模板

```text
你是标书图示规划助手。请阅读下方章节内容，为需要插图的位置生成 SVG 框图描述 JSON。

必须遵循：
1. 输出必须符合 `schema/svg_diagram.schema.json`，根对象为 {"documentTitle": "...", "figures": [...]}。
2. 图型只选用：
   - layered_architecture：总体架构、技术体系、数据体系；
   - flowchart：业务流程、处置闭环、实施路径；
   - swimlane_flowchart：跨角色、跨部门的责任流程；
   - sequence_diagram：接口调用、事件触发、消息交互；
   - capability_map：功能组成、能力清单；
   - relationship_map：包含系统域边界、复杂交互和多类箭头关系的架构图。
3. 使用内置 icon 标识增强表达：government, organization, user, admin, radiation, location, map,
   workflow, dashboard, report, form, database, shield, server, api, message, terminal,
   settings, alert, check, vehicle, sensor, cloud, network, lock, audit, ai,
   browser, mobile, camera, gps, gateway, queue, file, search, chart, calendar,
   bell, email, key, firewall, backup, cluster, monitor, upload, download, contract。
4. 不要输出 SVG 坐标、CSS 或 Mermaid 代码；只输出 JSON 描述。
5. 只使用章节中明确出现或能够直接归纳的内容；未确认的建设内容写入 note 说明。
6. 每张图提供 placement、title、subtitle 和 note。
7. 总体架构图每层建议 3 至 8 个节点；能力框图每分组建议 2 至 6 项；流程图的所有 edges 必须引用已有 node id。
8. 复杂关系图通过 containers 表示包含边界；edges 的 relation 仅选 flow、data、control、alert、sync，需要双向交互时设置 bidirectional: true。
9. 需要清晰正式的标书效果时，优先使用 relationship_map 表达多域关系，并避免一张图堆叠过多交叉线。
10. 接口和消息调用选择 sequence_diagram，使用 participants 与 messages；跨责任主体的业务流选择 swimlane_flowchart，使用 lanes、steps 与 edges。

章节内容：
---
{{在此粘贴标书章节内容}}
---

只返回 JSON，不要添加解释。
```

## 渲染步骤

将模型输出保存为 `diagram-spec.json` 后运行：

```powershell
python '.\src\generate_architecture_diagram.py' --spec '.\examples\diagram-spec.json' --validate-only
python '.\src\generate_architecture_diagram.py' --spec '.\examples\diagram-spec.json' --output '.\results\current\自定义输出' --theme clarity_blue --png
```

若校验提示未知图标或未知节点，将错误反馈给大模型要求仅修正 JSON，再重新执行生成命令。

## 数据图模板（ECharts 本地工作台）

需要呈现建设规模、覆盖率、能力评分或数据流向时，使用以下模板生成数据图 JSON，再导入本地 HTML 工作台。

```text
你是标书数据图规划助手。请阅读章节中明确提供的数据与关系，生成适用于标书插图的数据图描述 JSON。

必须遵循：
1. 输出必须符合 `schema/echarts_diagram.schema.json`，根对象为 {"documentTitle": "...", "charts": [...]}。
2. 图型只选用：
   - bar_line：同时展示数量趋势与百分比趋势；
   - radar：比较能力、指标或方案维度；
   - sankey：表达数据来源、汇聚与应用去向。
3. 每张图必须填写 title、note、source，并填写建议的 placement。
4. 不能将推测数值写成项目事实；没有已确认数据时，必须在 dataNotice 标注“演示数据，仅用于排版或能力表达验证”。
5. 只输出 JSON，不输出 ECharts option、JavaScript、SVG 或解释文字。

章节内容和已确认数据：
---
{{在此粘贴标书段落、数据表或关系说明}}
---
```

使用步骤：

```powershell
Start-Process '.\web\echarts-workbench\index.html'
```

在打开的页面导入模型生成的 JSON，人工确认标题、统计口径和注脚后，导出 SVG 插入正式文档。
