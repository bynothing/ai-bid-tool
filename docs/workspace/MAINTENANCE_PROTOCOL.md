# Maintenance Protocol

本文件规定项目记忆系统如何维护。

## 每次开发开始

执行：

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
Get-Content docs\workspace\ROADMAP.md -TotalCount 260
Get-Content docs\PROJECT_STRUCTURE.md -TotalCount 260
Get-Content docs\quality-targets\illustration\README.md -TotalCount 220
```

如果任务涉及配图架构，再读：

```powershell
Get-Content docs\workspace\KNOWLEDGE_MAP.md -TotalCount 260
Get-Content docs\workspace\DECISION_LOG.md -TotalCount 260
```

## 每次开发结束

至少更新其中一个：

- `STATE.md`：事实状态变化、测试结果、当前风险。
- `ROADMAP.md`：任务状态变化、阶段目标变化。
- `SESSION_HANDOFF.md`：下一次继续开发需要知道的具体上下文。
- `DECISION_LOG.md`：出现新的架构取舍。
- `docs/quality-targets/illustration/TODO.md`：配图质量目标或质量任务变化。
- `docs/quality-targets/illustration/RECORD.md`：配图质量评审、基线或参考目标变化。
- `docs/PROJECT_FEATURES.md`：新增或完成系统能力。
- `docs/PROJECT_TODO.md`：项目级任务状态变化。
- `docs/NAVIGATION.md`：入口或阅读路径变化。
- `docs/FILE_GOVERNANCE.md`：文件归位、命名、Git 跟踪规则变化。

如果修改影响用户命令、Schema、流水线逻辑、标书输出正确性，还必须更新：

- `CHANGELOG.md`

## 状态更新规则

`STATE.md` 只写当前事实：

- 当前验证命令和结果。
- 当前主要风险。
- 当前活跃模块。
- 新会话启动检查。

不要写：

- 长期愿景。
- 模糊计划。
- 未验证猜测。

## 任务更新规则

`ROADMAP.md` 中任务必须可验收。

好任务：

```text
梳理 decision.py，让 plan/manifest 显式包含 tier 与降级原因。
验收：新增测试覆盖 Tier 1 fallback 到 Tier 2 的 manifest 字段。
```

坏任务：

```text
优化配图效果。
```

## 决策更新规则

当出现以下情况，更新 `DECISION_LOG.md`：

- 选择一种架构路线，放弃另一种路线。
- 修改对外接口。
- 改变流水线阶段职责。
- 改变模板、渲染器、LLM 的分工。
- 引入新的质量门禁。

每条决策使用：

```text
## D-XXX：标题

日期：
状态：
背景：
决策：
原因：
影响：
```

## 交接更新规则

`SESSION_HANDOFF.md` 用于“下一次接着做”。它可以被覆盖，也可以按日期追加。

每次至少记录：

- 本次完成了什么。
- 改了哪些文件。
- 运行了哪些验证。
- 下一步最小可执行任务。
- 注意事项。

## 生成产物规则

- 临时 smoke 输出放在 `output/workspace_smoke` 或明确命名的临时目录。
- 验证后无保留价值应清理。
- 有保留价值的输出必须在 `STATE.md` 或相关 fixture 中说明用途。

## 搜索优先

查找文件用：

```powershell
rg --files
```

查找内容用：

```powershell
rg "pattern"
```

不要靠回忆猜文件路径。
