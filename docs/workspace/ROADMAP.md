# Roadmap

最后更新：2026-06-07

## 北极星

把自动配图从“生成一张图”升级为“可审计、可降级、可回归、可持续扩类的配图平台”。

质量目标：

- 高质量：图能准确解释技术方案和评分响应，不是装饰。
- 稳定：文字不爆框、元素不重叠、输出跨环境一致。
- 快速：主链路依赖结构化数据和确定性渲染，减少大模型反复生成。
- 高性价比：大模型只用于语义决策和必要修复，渲染与 QA 由代码完成。

## 阶段计划

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

状态：待启动。

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
- 现有 57 个测试通过，并新增决策层测试。

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

## 暂不做

- 不一次性模板化所有图型。
- 不让 LLM 直接生成复杂 SVG 坐标作为主路线。
- 不在旧版 `illustration/` 上继续堆新能力。
- 不把一次性输出目录当成质量基准。
