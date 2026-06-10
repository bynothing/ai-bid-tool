# Roadmap

最后更新：2026-06-08

## 北极星

把自动配图从“生成一张图”升级为“可审计、可降级、可回归、可持续扩类的配图平台”。

质量目标：

- 高质量：图能准确解释技术方案和评分响应，不是装饰。
- 稳定：文字不爆框、元素不重叠、输出跨环境一致。
- 快速：主链路依赖结构化数据和确定性渲染，减少大模型反复生成。
- 高性价比：大模型只用于语义决策和必要修复，渲染与 QA 由代码完成。

## 阶段计划

### Phase G：项目级总控与持续治理

状态：完成基础版，持续维护。

目标：

- 让整个标书自动化系统有统一的建设目标、现状、阶段路线、风险和下一步。
- 不让各专项文档彼此割裂。
- 每次开发都能回到工程项目级视角判断优先级。

关键文件：

- `docs/PROJECT_BUILD_OVERVIEW.md`
- `docs/PROJECT_FEATURES.md`
- `docs/PROJECT_TODO.md`
- `docs/NAVIGATION.md`
- `docs/FILE_GOVERNANCE.md`
- `AGENTS.md`
- `docs/workspace/STATE.md`
- `docs/workspace/ROADMAP.md`
- `docs/workspace/DECISION_LOG.md`
- `docs/PROJECT_STRUCTURE.md`

验收：

- 新会话能通过 `PROJECT_BUILD_OVERVIEW.md` 理解系统目标、当前能力、短板、主线和下一步。
- 项目级现状变化能回写到 `STATE.md` / `ROADMAP.md` / `SESSION_HANDOFF.md`。

### Phase Q：目标驱动的配图质量改造

状态：已建入口，A 类第一轮基线和首个实现路径已完成。

目标：

- 解决当前“图不好看、信息不清楚、箭头混乱、达不到工程级”的核心问题。
- 先由人工明确目标参考，再制定具体开发任务。
- 将主观质量问题转化为评分、Todo、fixture 和可回归验收。

关键文件：

- `docs/quality-targets/illustration/README.md`
- `docs/quality-targets/illustration/TARGET_BRIEF.md`
- `docs/quality-targets/illustration/ACCEPTANCE_RUBRIC.md`
- `docs/quality-targets/illustration/DEVELOPMENT_PLAN.md`
- `docs/quality-targets/illustration/TODO.md`
- `docs/quality-targets/illustration/CONTINUOUS_IMPROVEMENT_LOOP.md`
- `docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md`

验收：

- 至少 5 个人工参考目标有说明。
- 至少 3 个当前系统输出有评分和缺陷记录。
- 首批质量 Todo 能落到具体图型、渲染器或模板改造。
- 后续每轮质量优化都有 `RECORD.md` 或 fixture 记录。
- 已完成 2 个当前系统输出基线：A 类工艺流程 / 系统交互大图 86 / 100，D 类多层能力体系说明图 90 / 100。

当前第一轮：

- 原型：工艺流程 / 系统交互大图。
- 目标参考：`五菱总装A-H工艺段流程及系统交互点分析图 (1).png`。
- 计划入口：`docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md`。
- 当前实现：`process.interaction_map` 和 `architecture.layered_explainer` 均可自动路由 Draw.io，并已生成基线、评分和 fixture。

### Phase 0：信息系统与基线

状态：完成。

目标：

- 建立项目记忆系统，确保新会话可恢复上下文。
- 保持测试基线可运行。
- 明确当前工作区改动边界。

验收：

- `docs/workspace/` 入口完整。
- `WORKSPACE.md` 指向新体系。
- `python -m pytest` 通过。
- 记录当前配图 smoke 现状。

### Phase 1：决策层升级

状态：部分启动。

目标：

- 将 `renderer: "auto"` 升级为完整产出路径决策。
- 输出 Tier、模板、渲染器、降级原因、人工复核标记。
- 保证 manifest 能解释每张图为什么这样生成。

关键文件：

- `src/bid_tool/illustration_v2/core/decision.py`
- `src/bid_tool/illustration_v2/core/catalog.py`
- `src/bid_tool/illustration_v2/core/manifest.py`
- `src/bid_tool/illustration_v2/api.py`
- `src/bid_tool/schemas/illustration_job_v2.schema.json`

验收：

- `api.plan()` 可返回 tier、renderer、template、reason、fallback。
- fallback 不是静默发生，必须写入 manifest。
- 现有 62 个测试通过，并新增 `process.interaction_map` 与 `architecture.layered_explainer` 自动路由和结构测试。

### Phase 2：真实样本与质量评测

状态：待启动。

目标：

- 建立真实标书场景 fixture。
- 将主观质量问题转化为可回归样本。
- 建立图件质量评分表。

建议目录：

```text
tests/fixtures/illustration_cases/
  architecture_layered/
  interface_map/
  incident_response/
  inspection_taxonomy/
  security_loop/
  dense_topology/
  scoring_matrix/
```

每个 case 包含：

- `input.md`：章节片段或配图意图来源。
- `job.json`：期望结构化配图任务。
- `expected.md`：人工期望和验收点。
- `quality.md`：生成结果评分与缺陷记录。

验收：

- 至少 5 个真实高频图型有 fixture。
- 每个 fixture 可独立运行配图 smoke。
- 缺陷能被记录并复现。

### Phase 3：几何级 QA

状态：待启动。

目标：

- 让成功标准从“能生成文件”升级为“渲染结果合格”。
- 建立最小自动检查，先覆盖模板 SVG。

最低检查：

- 无 `data-fit="false"`。
- 关键文本不超出槽位。
- 关键元素不重叠。
- PNG 导出可读。
- 图题、图号、章节位置与 manifest 一致。

验收：

- QA 失败能在 manifest 或测试中暴露。
- 至少一个模板路径 fixture 覆盖几何 QA。

### Phase 4：模板扩类与成本优化

状态：待启动。

目标：

- 按真实使用频次扩充 Tier 1 模板。
- 对常见 fallback 场景进行模板化。
- 引入缓存策略，降低 LLM 与渲染成本。

优先图型：

1. `architecture.layered`
2. `relationship.platform_interface` / `integration.interface_map`
3. `process.severity_closure` / `operation.incident_response`
4. `taxonomy.inspection_cards` / `operation.inspection_taxonomy`
5. `security.closed_loop` / `architecture.security_ring`
6. `matrix.scoring_response`

验收：

- 高频图型优先命中 Tier 1。
- fallback 比例持续下降。
- smoke 和测试耗时可控。

## 当前任务板

| ID | 状态 | 任务 | 验收 |
| --- | --- | --- | --- |
| T-001 | 完成 | 建立项目记忆系统 | 新会话能通过 `WORKSPACE.md` 和 `docs/workspace/` 恢复上下文 |
| T-002 | 进行中 | 收敛旧版文档指向 | 旧 `illustration/` 入口不再作为新开发主入口 |
| T-003 | 待办 | 决策层字段梳理 | plan/manifest 显式包含 tier 与降级原因 |
| T-004 | 待办 | 建立真实样本 fixture | 至少 5 个图型可复现 |
| T-005 | 待办 | 几何 QA 最小实现 | 模板 SVG 可自动发现文本 fit 失败 |
| T-006 | 待办 | S5 prompt 与能力目录对齐 | AI 输出只依赖当前 v2 能力 |
| T-007 | 完成 | 整理项目文件结构 | 长期架构与标准文档迁到 `docs/`，并新增 `docs/PROJECT_STRUCTURE.md` |
| T-008 | 完成 | 建立配图质量目标区 | `docs/quality-targets/illustration/` 包含目标、评分、计划、Todo、记录和参考素材入口 |
| T-009 | 待办 | 人工补充配图参考目标 | 至少 5 个参考图有说明，并进入 `references/` / `reviews/` |
| T-010 | 进行中 | 建立当前配图质量基线 | 已完成 2 个基线，仍需至少 1 个当前输出按 Rubric 评分 |
| T-011 | 完成 | 执行配图质量第一轮迭代 | 已生成系统交互大图基线，完成评分、契约草案和首个 Draw.io 实现路径 |
| T-012 | 完成 | 建立项目级建设总控 | `docs/PROJECT_BUILD_OVERVIEW.md` 汇总目标、现状、主线、路线、门禁和下一步 |
| T-013 | 完成 | 建立项目级功能和 TODO 清单 | `docs/PROJECT_FEATURES.md` 与 `docs/PROJECT_TODO.md` 可持续维护 |
| T-014 | 完成 | 治理人/智能体文件阅读架构 | 新增 `AGENTS.md`、`docs/NAVIGATION.md`、`docs/FILE_GOVERNANCE.md` 和源码模块地图 |

## 暂不做

- 不一次性模板化所有图型。
- 不让 LLM 直接生成复杂 SVG 坐标作为主路线。
- 不在旧版 `illustration/` 上继续堆新能力。
- 不把一次性输出目录当成质量基准。
