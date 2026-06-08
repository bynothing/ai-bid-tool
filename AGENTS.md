# Agent Startup Guide

本文件面向进入 `bid-tool` 的智能体。目标是让智能体不用长期记忆，也能快速、稳定、少走弯路地继续开发。

## 必读顺序

每次开始前按顺序读取：

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
```

如果任务涉及配图质量，再读：

```powershell
Get-Content docs\quality-targets\illustration\README.md -TotalCount 220
Get-Content docs\quality-targets\illustration\TODO.md -TotalCount 260
Get-Content docs\quality-targets\illustration\ITERATION_001_PROCESS_INTERACTION.md -TotalCount 260
```

## 当前主线

当前项目优先级以 `docs/PROJECT_TODO.md` 为准。

当前最高优先级：

```text
P0-001 / IQ-008
生成系统交互大图当前基线
  -> 保存 job/manifest/output
  -> 按 Rubric 打分
  -> 转成契约草案和开发任务
```

## 文件边界

- 运行时代码放 `src/bid_tool/`。
- 项目级文档放 `docs/`。
- 当前状态和交接放 `docs/workspace/`。
- 配图质量目标放 `docs/quality-targets/illustration/`。
- 大型参考图片放 `docs/quality-targets/illustration/references/`，默认本地使用，不提交 Git。
- 临时输出放 `output/workspace_smoke/` 或明确临时目录，验证后清理。

详细规则见：

```text
docs/FILE_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
```

## 开发纪律

- 不要回滚用户或既有未提交改动。
- 修改用户可见命令、Schema、流水线逻辑、输出正确性时，更新 `CHANGELOG.md`。
- 完成任务后更新 `docs/PROJECT_TODO.md`、`docs/workspace/STATE.md` 或 `docs/workspace/SESSION_HANDOFF.md`。
- 配图质量任务还要更新 `docs/quality-targets/illustration/RECORD.md`。
- 优先把可复现质量问题沉淀为 fixture，而不是只修单张图。

## 验证

通用验证：

```powershell
python -m pytest
```

配图 smoke：

```powershell
python -m bid_tool.illustration_v2.toolkit --job "examples\示例_配图平台v2任务.json" --output "output\workspace_smoke" --png
```

验证完成后，若 `output/workspace_smoke` 无保留价值，应清理。
