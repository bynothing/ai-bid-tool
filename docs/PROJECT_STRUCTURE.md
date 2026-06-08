# Project Structure

最后更新：2026-06-07

本文档规定 `bid-tool` 当前项目文件结构，以及新增文件应该放在哪里。

## 顶层结构

```text
bid-tool/
  README.md                         项目总说明与用户入口
  WORKSPACE.md                      持续开发入口和项目记忆系统入口
  AGENTS.md                         智能体启动协议
  CHANGELOG.md                      重大修改记录
  pyproject.toml                    Python 包、依赖、命令入口
  docs/                             项目级文档
  entrypoint/                       兼容入口，指向 WORKSPACE/docs
  examples/                         用户可运行示例 Job
  src/bid_tool/                     Python 源码
  tests/                            自动化测试
  tools/                            本地工具脚本
  output/                           生成产物和验证输出
  reference_output/                 历史参考输出
```

## docs/

```text
  docs/
    README.md
    NAVIGATION.md
    FILE_GOVERNANCE.md
    PROJECT_BUILD_OVERVIEW.md
    PROJECT_FEATURES.md
    PROJECT_TODO.md
    PROJECT_STRUCTURE.md
  workspace/
    README.md
    STATE.md
    ROADMAP.md
    DECISION_LOG.md
    KNOWLEDGE_MAP.md
    MAINTENANCE_PROTOCOL.md
    SESSION_HANDOFF.md
  architecture/
    illustration-v2/
      README.md
      current-architecture.md
      stable-svg-rendering.md
      agent-execution-environment-design.md
      agent-execution-environment-plan.md
      refactor-goal.md
      decision-analysis.md
  standards/
    illustration/
      README.md
      drawing-content-standard.md
      drawio-integration.md
  quality-targets/
    illustration/
      README.md
      TARGET_BRIEF.md
      REFERENCE_INTAKE_TEMPLATE.md
      ACCEPTANCE_RUBRIC.md
      DEVELOPMENT_PLAN.md
      TODO.md
      RECORD.md
      references/
      generated-baselines/
      reviews/
  methodology/
    README.md
    agent-complex-engineering-methodology.md
```

放置规则：

- `workspace/`：当前状态、阶段计划、决策日志、交接记录。
- `architecture/`：系统设计、重构方案、长期架构说明。
- `standards/`：绘图内容规范、质量标准、交付标准。
- `quality-targets/`：人工参考目标、质量评分、持续 Todo、基线和评审记录。
- `methodology/`：从项目实践提炼的方法论和分享材料。
- 新增长期文档优先放 `docs/`，不要放进 `src/`。

## src/bid_tool/

```text
src/bid_tool/
  README.md                         源码模块地图
  cli.py                            bid-tool 命令入口
  pipeline/                         9 阶段标书流水线
  prompts/                          LLM Prompt 模板
  profiles/                         项目类型配置
  schemas/                          对外 JSON Schema 与 AI 接口协议
  illustration_v2/                  当前配图执行环境
```

放置规则：

- 运行时代码放 `src/bid_tool/`。
- 对外 Schema 放 `src/bid_tool/schemas/`。
- Prompt 放 `src/bid_tool/prompts/`。
- 不把项目长期计划、会话交接、架构讨论文档放进 `src/`。

## src/bid_tool/illustration_v2/

```text
illustration_v2/
  README.md                         配图执行环境源码地图
  api.py                            Python API
  toolkit.py                        bid-illustrate CLI
  standalone.py                     独立工具包构建
  core/                             Job、目录、决策、校验、manifest、文本测量
  renderers/                        template_svg、drawio、组件库等渲染器
  templates/                        模板契约、模板说明、template.svg
  catalogs/                         能力目录
  examples/                         包内示例 Job
  materials/                        参考素材与分析
```

放置规则：

- 模板契约与模板说明留在 `templates/`，因为它们是执行环境能力的一部分。
- 能力目录留在 `catalogs/`。
- 参考素材留在 `materials/`。
- 面向人的项目级绘图标准放 `docs/standards/illustration/`。

## tests/

```text
tests/
  test_*.py                         单元与集成测试
  fixtures/                         建议新增真实样本 fixture
```

建议新增：

```text
tests/fixtures/illustration_cases/
  architecture_layered/
  interface_map/
  incident_response/
  inspection_taxonomy/
  security_loop/
```

每个真实样本 case 建议包含：

```text
input.md
job.json
expected.md
quality.md
```

## output/

`output/` 是生成产物目录。不要把临时输出当作源代码事实。

规则：

- 临时 smoke 输出使用 `output/workspace_smoke`。
- 验证后无保留价值应清理。
- 如果某个输出需要保留，必须在 `docs/workspace/STATE.md` 或 fixture 中说明用途。

## 文件归位速查

| 新内容 | 应放位置 |
| --- | --- |
| 新 CLI 或运行时代码 | `src/bid_tool/` |
| 新流水线阶段逻辑 | `src/bid_tool/pipeline/stages/` |
| 新 Prompt | `src/bid_tool/prompts/` |
| 新 JSON Schema | `src/bid_tool/schemas/` |
| 新配图模板 | `src/bid_tool/illustration_v2/templates/` |
| 新配图渲染器 | `src/bid_tool/illustration_v2/renderers/` |
| 新配图能力目录项 | `src/bid_tool/illustration_v2/catalogs/` |
| 新项目状态 | `docs/workspace/STATE.md` |
| 新导航规则 | `docs/NAVIGATION.md` |
| 新文件治理规则 | `docs/FILE_GOVERNANCE.md` |
| 新任务计划 | `docs/workspace/ROADMAP.md` |
| 新项目级建设总控 | `docs/PROJECT_BUILD_OVERVIEW.md` |
| 新已完成功能记录 | `docs/PROJECT_FEATURES.md` |
| 新项目级 TODO | `docs/PROJECT_TODO.md` |
| 新架构决策 | `docs/workspace/DECISION_LOG.md` |
| 新架构方案 | `docs/architecture/` |
| 新内容/质量标准 | `docs/standards/` |
| 新人工参考目标 | `docs/quality-targets/` |
| 新方法论分享 | `docs/methodology/` |
| 新配图质量 Todo | `docs/quality-targets/illustration/TODO.md` |
| 新配图人工评审 | `docs/quality-targets/illustration/reviews/` |
| 新真实样本 | `tests/fixtures/` |
| 临时生成结果 | `output/` |

## 当前整理原则

- 先整理文档和入口，再整理源码。
- 不移动运行时代码，除非有测试覆盖和明确迁移计划。
- 不回滚当前工作区已有迁移改动。
- `src/bid_tool/illustration_v2/` 是当前新开发主线。
- 旧版 `src/bid_tool/illustration/` 不再作为新能力入口。
