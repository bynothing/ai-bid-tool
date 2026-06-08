# Workspace Memory System

本目录是 `bid-tool` 的项目记忆系统。目标是让任何一次新开发会话都能通过快速读取文件恢复上下文，而不是依赖智能体长期记忆。

## 读取顺序

新会话进入项目后，按下面顺序读取：

1. `WORKSPACE.md`：项目根入口，确认真实目录、核心问题和工作纪律。
2. `docs/workspace/STATE.md`：当前事实状态，包括分支、测试基线、活跃焦点、风险。
3. `docs/PROJECT_BUILD_OVERVIEW.md`：工程项目级建设总控。
4. `docs/PROJECT_FEATURES.md`：已完成功能和能力成熟度。
5. `docs/PROJECT_TODO.md`：全工程 TODO 队列。
6. `docs/NAVIGATION.md`：按任务类型导航。
7. `docs/FILE_GOVERNANCE.md`：文件治理和 Git 跟踪规则。
8. `docs/workspace/ROADMAP.md`：当前阶段目标、任务队列和验收标准。
9. `docs/PROJECT_STRUCTURE.md`：当前文件结构和新增文件归位规则。
10. 按需读取：
   - `docs/workspace/KNOWLEDGE_MAP.md`：业务背景、配图体系、关键模块地图。
   - `docs/workspace/DECISION_LOG.md`：重要架构决策和原因。
   - `docs/workspace/MAINTENANCE_PROTOCOL.md`：如何更新这些文件。
   - `docs/workspace/SESSION_HANDOFF.md`：每次开发结束时的交接模板。

## 信息分层

| 文件 | 更新频率 | 作用 |
| --- | --- | --- |
| `STATE.md` | 每次开发会话 | 记录当前工作区事实和最新验证结果 |
| `ROADMAP.md` | 每个阶段或任务变化 | 管理阶段计划、任务板、验收口径 |
| `DECISION_LOG.md` | 每个关键决策 | 记录为什么这样设计，避免重复争论 |
| `KNOWLEDGE_MAP.md` | 背景知识变化时 | 记录项目背景、概念、模块地图和查找路径 |
| `MAINTENANCE_PROTOCOL.md` | 很少 | 规定信息系统如何维护 |
| `SESSION_HANDOFF.md` | 每次收尾可追加或覆盖 | 给下一次开发的交接摘要 |

## 快速恢复命令

```powershell
cd D:\AI_native_change\bid-tool
git status --short --branch
python -m pytest
```

配图 smoke：

```powershell
python -m bid_tool.illustration_v2.toolkit --job "examples\示例_配图平台v2任务.json" --output "output\workspace_smoke" --png
```

smoke 输出验证后，如无保留价值，应删除临时目录：

```powershell
$target = Resolve-Path -LiteralPath "output\workspace_smoke"
$root = Resolve-Path -LiteralPath "."
if ($target.Path.StartsWith($root.Path + [System.IO.Path]::DirectorySeparatorChar)) {
  Remove-Item -LiteralPath $target.Path -Recurse -Force
}
```

## 维护原则

- 状态写事实，不写愿望。
- 任务写可验收动作，不写空泛方向。
- 决策写取舍原因，不只写结论。
- 背景知识写可复用概念和查找路径，不重复整篇已有文档。
- 所有重大修改必须同步更新 `CHANGELOG.md`，遵守根 `README.md` 的约定。
