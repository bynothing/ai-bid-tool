# File Governance

最后更新：2026-06-07

本文档规定 `bid-tool` 的文件管理规则。目标是让人和智能体都能快速判断：

- 文件应该放在哪里。
- 什么应该进 Git。
- 什么只作为本地素材或临时产物。
- 如何命名、索引和维护。

## 核心原则

1. 入口少而稳定：根入口、项目总控、功能清单、TODO、结构说明。
2. 源码和项目知识分离：运行时代码在 `src/`，长期知识在 `docs/`。
3. 大二进制默认不入库：参考图片和生成图片可本地使用，说明和索引入库。
4. 可复现优先：重要样本尽量沉淀为 job、manifest、fixture，而不是只保存截图。
5. 状态及时维护：每次开发结束更新对应状态、TODO、记录。

## Git 跟踪规则

### 应该提交

- 源码：`src/bid_tool/`
- 测试：`tests/`
- 示例 Job：`examples/`
- 工具脚本：`tools/`
- 项目文档：`docs/**/*.md`
- Schema、Prompt、模板契约。
- 小型、必要、可复现的基准说明文件。

### 默认不提交

- 临时输出：`output/workspace_smoke/`
- 临时实验目录：`.tmp_illustration_v2_*/`
- 大型人工参考图片：`docs/quality-targets/illustration/references/*`
- 大型生成基线图片：`docs/quality-targets/illustration/generated-baselines/*`
- 本地工具缓存：`.tools/`

例外：

- `references/README.md`、`generated-baselines/README.md`、`.gitkeep` 可提交。
- 如果某张参考图必须成为长期公共基准，应先压缩、命名、写明来源和用途，再单独评估是否入库。

## 顶层入口规则

| 文件 | 作用 |
| --- | --- |
| `README.md` | 用户入口，讲怎么安装和运行 |
| `WORKSPACE.md` | 持续开发入口 |
| `AGENTS.md` | 智能体启动协议 |
| `CHANGELOG.md` | 重大变更历史 |
| `docs/NAVIGATION.md` | 人和智能体导航 |
| `docs/PROJECT_BUILD_OVERVIEW.md` | 工程项目级总控 |
| `docs/PROJECT_FEATURES.md` | 已完成能力 |
| `docs/PROJECT_TODO.md` | 全工程任务队列 |
| `docs/PROJECT_STRUCTURE.md` | 目录结构和放置规则 |

## 命名规则

### 文档

- 项目级核心文档使用大写蛇形：`PROJECT_TODO.md`。
- 专项文档可使用大写标题：`ACCEPTANCE_RUBRIC.md`。
- 长期架构文档可使用 kebab-case：`current-architecture.md`。
- 评审记录建议：`reviews/YYYYMMDD-topic.md`。

### 测试样本

```text
tests/fixtures/<domain>/<case_name>/
  input.md
  job.json
  expected.md
  quality.md
```

### 生成基线

```text
docs/quality-targets/illustration/generated-baselines/YYYYMMDD-topic/
  README.md
  job.json
  manifest.json
  review.md
```

大型图片可留在本地同目录，但默认被 `.gitignore` 忽略。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `docs/workspace/` | 当前状态、路线、决策、交接 |
| `docs/architecture/` | 长期架构和系统工程设计 |
| `docs/standards/` | 标准、规范、质量门禁 |
| `docs/quality-targets/` | 人工质量目标、评分、评审和 Todo |
| `src/bid_tool/` | 运行时代码 |
| `src/bid_tool/schemas/` | 对外 JSON Schema |
| `src/bid_tool/prompts/` | LLM Prompt |
| `src/bid_tool/illustration_v2/templates/` | 运行时模板契约和模板资产 |
| `tests/` | 自动化测试与 fixture |
| `examples/` | 用户可运行示例 |
| `output/` | 生成产物，默认不是知识源 |
| `tools/` | 本地辅助脚本 |

## 维护检查清单

新增文件时问：

- 这是运行时代码吗？是则放 `src/`。
- 这是项目知识/计划/状态吗？是则放 `docs/`。
- 这是测试样本吗？是则放 `tests/fixtures/`。
- 这是临时输出吗？是则放 `output/`，并考虑清理。
- 这是大型二进制吗？默认不要提交。

开发结束时问：

- `PROJECT_TODO.md` 状态是否要改？
- `PROJECT_FEATURES.md` 是否新增能力？
- `STATE.md` 是否记录了验证结果？
- `SESSION_HANDOFF.md` 是否能让下一次接上？
- `CHANGELOG.md` 是否需要更新？

## 当前治理状态

- 已建立人类入口：`README.md`、`WORKSPACE.md`、`docs/NAVIGATION.md`。
- 已建立智能体入口：`AGENTS.md`。
- 已建立项目总控：`PROJECT_BUILD_OVERVIEW.md`。
- 已建立功能/TODO：`PROJECT_FEATURES.md`、`PROJECT_TODO.md`。
- 已建立配图质量目标区。
- 已通过 `.gitignore` 管理大型参考图和生成基线。
