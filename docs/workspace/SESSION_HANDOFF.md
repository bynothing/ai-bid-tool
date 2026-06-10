# Session Handoff

最后更新：2026-06-08

## 本次完成

- 创建 `docs/workspace/` 项目记忆系统。
- 建立状态、路线图、决策日志、知识地图、维护协议和交接模板。
- 根 `WORKSPACE.md` 已作为项目工作入口。
- `entrypoint/ENTRYPOINT.md` 已改为兼容入口，指向新的项目记忆系统。
- 外层 `bid-tool.code-workspace` 已指向真实项目目录。
- 新增 `docs/PROJECT_STRUCTURE.md`，规定项目目录结构和新增文件归位规则。
- 新增 `docs/PROJECT_BUILD_OVERVIEW.md`，作为工程项目级建设总控。
- 新增 `docs/PROJECT_FEATURES.md`，记录已完成功能和能力成熟度。
- 新增 `docs/PROJECT_TODO.md`，记录全工程 TODO 队列。
- 新增 `AGENTS.md`，作为智能体启动协议。
- 新增 `docs/NAVIGATION.md`，作为人和智能体任务导航。
- 新增 `docs/FILE_GOVERNANCE.md`，作为文件归位、命名、Git 跟踪和产物治理规则。
- 新增源码模块地图：`src/bid_tool/README.md`、`src/bid_tool/pipeline/README.md`、`src/bid_tool/schemas/README.md`、`src/bid_tool/illustration_v2/README.md`。
- 长期架构文档迁移到 `docs/architecture/illustration-v2/`。
- 配图标准文档迁移到 `docs/standards/illustration/`。
- 新增 `docs/quality-targets/illustration/`，用于人工提供配图参考目标、持续 Todo、评分标准和迭代记录。
- 新增 `docs/methodology/agent-complex-engineering-methodology.md`，把当前整套持续开发要求沉淀为“智能体开发复杂工程应用的方法论”分享文档。
- 新增 `process.interaction_map` 初版能力：`renderer: auto` 自动路由 Draw.io，支持工艺段分区、主流程、辅助/回流关系、图例和术语说明。
- 新增回归样本：`tests/fixtures/illustration_cases/process_interaction_map/job.json`。
- 生成 A 类基线：`docs/quality-targets/illustration/generated-baselines/iteration-001-process-interaction/`。
- 新增基线评审：`docs/quality-targets/illustration/reviews/baseline-process-interaction-iteration-001.md`，当前评分 86 / 100。
- 优化 `process.interaction_map`：长图例自动转底部图例，物料/异常走下方通道，返修/回流走上方通道，并增加语义线色。
- 继续优化 `process.interaction_map`：返修/回流线改为外侧顶部绕行，避开 C/D 主流程交界。
- 继续优化 `process.interaction_map`：工艺段与节点增加语义配色，底部图例进一步压缩，整体布局更紧凑。
- 新增 `architecture.layered_explainer`：参考用户提供的“AI 系统七层架构全景图”，支持左编号层级、中部层名/图标、右说明和底部类比区。
- 新增回归样本：`tests/fixtures/illustration_cases/layered_explainer/job.json`。
- 新增基线评审：`docs/quality-targets/illustration/reviews/baseline-layered-explainer-iteration-002.md`，当前评分 90 / 100。

## 本次验证

```powershell
python -m pytest
```

结果：

```text
57 passed
```

配图 smoke：

```powershell
python -m bid_tool.illustration_v2.toolkit --job "examples\示例_配图平台v2任务.json" --output "output\workspace_smoke" --png
```

结果：

```text
rendered 4 asset(s)
```

临时输出已清理。

文件结构整理后已再次执行 `python -m pytest` 和同一配图 smoke，结果正常，临时输出已清理。

输出方法论文档后再次执行：

```powershell
python -m pytest
```

结果：

```text
57 passed
```

完成 `process.interaction_map` 初版后再次执行：

```powershell
python -m pytest
```

结果：

```text
59 passed
```

优化主辅流程通道和底部图例后再次执行：

```powershell
python -m pytest
```

结果：

```text
60 passed
```

优化回流线外侧绕行后再次执行：

```powershell
python -m pytest
```

结果：

```text
60 passed
```

优化颜色和整体布局后再次执行：

```powershell
python -m pytest
```

结果：

```text
60 passed
```

新增 `architecture.layered_explainer` 后再次执行：

```powershell
python -m pytest
```

结果：

```text
62 passed
```

## 下一次最小可执行任务

从 `T-002` 或 `T-003` 开始：

- `T-002`：收敛旧版文档指向，避免新开发继续读旧 `illustration/`。
- `T-003`：梳理 `src/bid_tool/illustration_v2/core/decision.py`，让 plan/manifest 显式包含 tier 与降级原因。

推荐先做 `T-003`，因为它直接影响“高质量、稳定、快速、高性价比”的自动配图主线。

如果继续处理“配图不好看、不清楚、箭头混乱”的问题，优先从 `docs/quality-targets/illustration/TODO.md` 开始，先补人工参考图和当前输出基线。

当前参考图已经达到 87 张，并已建立持续改进闭环和第一轮迭代计划。`IQ-008` 已完成：A 类“工艺流程 / 系统交互大图”已有基线、manifest、PNG/SVG/Draw.io 输出和评分记录。

工程项目级建设总控已建立在 `docs/PROJECT_BUILD_OVERVIEW.md`。新会话应在 `STATE.md` 后读取它，用于理解系统目标、现状、主线、阶段路线、质量门禁和下一步。

项目级已完成功能和 TODO 队列已建立：

- `docs/PROJECT_FEATURES.md`
- `docs/PROJECT_TODO.md`

下一步开发优先以 `PROJECT_TODO.md` 的 P0 队列为准。`P0-001 / IQ-008` 已完成，建议继续推进：

- `P0-002`：补足至少 3 个当前配图输出基线。
- design tokens：将当前工艺段配色、系统节点配色、线型语义抽成共享策略。
- icon token：为层级说明图、能力图、方法论图建立稳定图标映射。
- 回流线长度压缩：当前外侧绕行清晰但路径偏长。
- 自动 QA：将主流程缺失、图例缺失、边数量预算、线型语义写入可测试规则。
- `P0-005`：让 S5 prompt 能稳定产出 `process.interaction_map` 契约字段。

文件管理架构已治理完成：人类先看 `README.md` / `WORKSPACE.md` / `docs/NAVIGATION.md`，智能体先看 `AGENTS.md`。文件归位和大文件入库规则以 `docs/FILE_GOVERNANCE.md` 为准。源码阅读入口已补在 `src/bid_tool/README.md`、`src/bid_tool/pipeline/README.md`、`src/bid_tool/schemas/README.md`、`src/bid_tool/illustration_v2/README.md`。

方法论分享已保存到 `docs/methodology/agent-complex-engineering-methodology.md`，可作为对外或团队内部复盘材料，也可以继续扩展成培训稿、PPT 或项目建设 SOP。

## 注意事项

- 当前工作区已有大量未提交改动，不要回滚。
- 旧版 `src/bid_tool/illustration/` 在当前工作区表现为删除迁移。
- 新开发主入口是 `src/bid_tool/illustration_v2/`。
- 示例 Job 可 smoke，但不能代表真实质量。
- `process.interaction_map` 当前仍是 Tier 2 实现，manifest 会标记 `needs_human_review=true`；86 分是阶段性 B 级候选，不是最终目标级模板。
