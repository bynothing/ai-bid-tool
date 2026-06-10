# Current State

最后更新：2026-06-08

## 项目位置

```text
D:\AI_native_change\bid-tool
```

外层工作空间文件：

```text
C:\Users\杨辉\Documents\自动标书项目\bid-tool.code-workspace
```

## 当前目标

围绕标书自动生成项目，持续建设一个高质量、稳定、快速、高性价比的自动配图能力。

当前核心判断：

```text
LLM 负责语义理解、图型选择、模板选择、结构化 Job 填充。
确定性软件负责契约校验、排版、渲染、几何 QA、manifest 留痕。
```

## 当前工作区事实

- Git 分支：`main...origin/main`
- 工作区已有大量未提交改动。
- 旧版 `src/bid_tool/illustration/` 已在工作区表现为删除迁移。
- 当前活跃实现集中在 `src/bid_tool/illustration_v2/`。
- 本轮新增项目记忆系统目录：`docs/workspace/`。
- 本轮新增根入口：`WORKSPACE.md`。
- 本轮新增项目结构说明：`docs/PROJECT_STRUCTURE.md`。
- 长期架构文档已从 `src/bid_tool/devlop-plan/` 迁移到 `docs/architecture/illustration-v2/`。
- 配图内容标准已从 `src/bid_tool/illustration_v2/` 迁移到 `docs/standards/illustration/`。
- 本轮新增配图质量目标区：`docs/quality-targets/illustration/`，用于人工参考目标、评分标准、持续 Todo 和评审记录。
- 参考图已达到 87 张，并已初步归纳为 4 类目标原型。
- 第一轮质量改造计划已建立：`docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md`。
- 本轮新增工程项目级建设总控：`docs/PROJECT_BUILD_OVERVIEW.md`。
- 本轮新增已完成功能清单：`docs/PROJECT_FEATURES.md`。
- 本轮新增全工程 TODO 队列：`docs/PROJECT_TODO.md`。
- 本轮新增人和智能体导航：`docs/NAVIGATION.md`。
- 本轮新增文件治理规则：`docs/FILE_GOVERNANCE.md`。
- 本轮新增智能体启动协议：`AGENTS.md`。
- 本轮新增源码模块地图：`src/bid_tool/README.md`、`src/bid_tool/pipeline/README.md`、`src/bid_tool/schemas/README.md`、`src/bid_tool/illustration_v2/README.md`。
- 本轮新增方法论分享：`docs/methodology/agent-complex-engineering-methodology.md`，将本项目的复杂工程建设方式沉淀为可复用方法。
- 本轮新增 `process.interaction_map` 初版，支持工艺段分区、主流程、辅助/回流关系、图例和术语说明，并可由 `renderer: auto` 自动路由到 Draw.io。
- 本轮完成 A 类工艺流程 / 系统交互大图基线、评分和 fixture，并完成主辅流程通道、底部图例、回流线外侧绕行、语义配色和整体布局优化。
- 本轮根据用户提供的“AI 系统七层架构全景图”参考图，新增 D 类 `architecture.layered_explainer` 多层能力体系说明图。

重要提醒：不要回滚现有未提交改动。任何新修改都要先用 `git status --short --branch` 确认边界。

## 已验证基线

2026-06-07 验证：

```powershell
python -m pytest
```

结果：

```text
57 passed
```

2026-06-07 文件结构整理后复验：

```text
57 passed
```

2026-06-07 配图 smoke：

```powershell
python -m bid_tool.illustration_v2.toolkit --job "examples\示例_配图平台v2任务.json" --output "output\workspace_smoke" --png
```

结果：

```text
rendered 4 asset(s)
```

观察：

- `overall_architecture` 当前走 `structured_svg_fallback`。
- `coverage_trend`、`implementation_gantt`、`risk_matrix` 当前走 `free_svg_floor`。
- 这说明主链路可运行，但模板命中率和决策层能力仍是下一阶段重点。
- 临时输出 `output\workspace_smoke` 已清理。
- 文件结构整理后再次运行同一 smoke，结果正常，临时输出已清理。

2026-06-07 建立配图质量目标区后复验：

```text
57 passed
```

2026-06-07 参考图盘点与持续闭环计划后复验：

```text
57 passed
```

2026-06-07 建立项目级建设总控后复验：

```text
57 passed
```

2026-06-07 建立项目级 Features/TODO 后复验：

```text
57 passed
```

2026-06-07 治理文件管理架构后复验：

```text
57 passed
```

2026-06-08 输出智能体复杂工程方法论后复验：

```text
57 passed
```

2026-06-08 完成 `process.interaction_map` 初版和 A 类基线后复验：

```text
59 passed
```

2026-06-08 优化 `process.interaction_map` 主辅流程通道和底部图例后复验：

```text
60 passed
```

2026-06-08 优化 `process.interaction_map` 回流线外侧绕行后复验：

```text
60 passed
```

2026-06-08 优化 `process.interaction_map` 颜色和整体布局后复验：

```text
60 passed
```

2026-06-08 新增 `architecture.layered_explainer` 后复验：

```text
62 passed
```

基线产物：

```text
docs/quality-targets/illustration/generated-baselines/iteration-001-process-interaction/
```

评分：

```text
86 / 100
```

D 类多层能力体系说明图评分：

```text
90 / 100
```

文件管理治理结果：

- `AGENTS.md` 成为智能体启动协议。
- `docs/NAVIGATION.md` 成为人和智能体导航页。
- `docs/FILE_GOVERNANCE.md` 成为文件归位、命名、Git 跟踪和产物治理规则。
- `src/bid_tool/README.md`、`pipeline/README.md`、`schemas/README.md`、`illustration_v2/README.md` 成为源码阅读地图。
- `.gitignore` 已忽略大型参考图和生成基线产物，只保留说明/索引文件。
- `docs/methodology/` 成为项目实践方法论沉淀区，当前已形成一篇可分享的方法论文档。
- `process.interaction_map` 已进入 API 文档、fixture、测试和质量评审闭环，当前为 Tier 2 B 级候选实现。
- `architecture.layered_explainer` 已进入 API 文档、fixture、测试和质量评审闭环，当前为 Tier 2 A- 目标级基线候选。

## 当前关键风险

1. 既有未提交改动较多，后续开发容易混入无关修改。
2. 旧文档中仍有指向旧版 `illustration/` 的内容，需要逐步收敛到 `illustration_v2/`。
3. 示例 Job 多数图仍走 fallback，说明高质量 Tier 1 模板覆盖不足。
4. `process.interaction_map` 当前评分 86 / 100，design tokens、回流线长度压缩和自动 QA 仍需优化。
5. 当前“成功”主要由结构校验和渲染完成定义，几何级 QA 仍需要加强。
6. S5 侧 prompt、Schema、能力目录之间可能存在版本漂移。

## 当前推荐下一步

1. 推进 design tokens，将工艺段配色、系统节点配色、层级说明图配色、主辅线型语义抽成可复用策略。
2. 为 `architecture.layered_explainer` 增加 icon token 映射，替换当前文本缩写图标。
3. 建立自动视觉 QA 草案，优先覆盖主流程缺失、图例缺失、边数量预算、线型语义和文本容量。
4. 执行 `P0-002`：再建立至少 1 个当前系统输出基线，补足 3 个基线评分。
4. 更新 S5 prompt 与 `AI_ILLUSTRATION_API_V2.md`，确保 AI 能生成当前 `process.interaction_map` 契约字段。
5. 建立至少 2 个新的当前输出基线，完成 `P0-002`。
6. 建立真实样本基准集，覆盖至少 5 个高频标书图型。

## 新会话启动检查

```powershell
cd D:\AI_native_change\bid-tool
git status --short --branch
Get-Content WORKSPACE.md -TotalCount 220
Get-Content docs\workspace\STATE.md -TotalCount 220
Get-Content docs\PROJECT_BUILD_OVERVIEW.md -TotalCount 260
Get-Content docs\PROJECT_FEATURES.md -TotalCount 260
Get-Content docs\PROJECT_TODO.md -TotalCount 260
Get-Content docs\NAVIGATION.md -TotalCount 260
Get-Content docs\FILE_GOVERNANCE.md -TotalCount 260
Get-Content docs\methodology\agent-complex-engineering-methodology.md -TotalCount 260
Get-Content docs\workspace\ROADMAP.md -TotalCount 260
Get-Content docs\PROJECT_STRUCTURE.md -TotalCount 260
Get-Content docs\quality-targets\illustration\README.md -TotalCount 220
Get-Content docs\quality-targets\illustration\TODO.md -TotalCount 260
Get-Content docs\quality-targets\illustration\ITERATION_001_PROCESS_INTERACTION.md -TotalCount 260
```

如果要改配图相关代码，再读：

```powershell
Get-Content docs\workspace\KNOWLEDGE_MAP.md -TotalCount 260
Get-Content docs\workspace\DECISION_LOG.md -TotalCount 260
```
