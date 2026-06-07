# bid-tool Workspace Entrypoint

本文件是兼容入口。当前项目记忆系统已经迁移到：

```text
docs/workspace/
```

新会话请按顺序读取：

1. `WORKSPACE.md`
2. `docs/workspace/STATE.md`
3. `docs/workspace/ROADMAP.md`
4. `docs/workspace/KNOWLEDGE_MAP.md`
5. `docs/workspace/DECISION_LOG.md`

维护规则：

```text
docs/workspace/MAINTENANCE_PROTOCOL.md
```

## 当前主线

当前新开发主入口是：

```text
src/bid_tool/illustration_v2/
```

旧版 `src/bid_tool/illustration/` 正在迁移删除，不再作为新能力开发入口。

## 快速恢复

```powershell
cd D:\AI_native_change\bid-tool
git status --short --branch
Get-Content WORKSPACE.md -TotalCount 220
Get-Content docs\workspace\STATE.md -TotalCount 220
Get-Content docs\workspace\ROADMAP.md -TotalCount 260
Get-Content docs\PROJECT_STRUCTURE.md -TotalCount 260
```

## 当前核心问题

如何在标书正文基础上，构建高质量、稳定、快速、高性价比的自动配图能力。

当前路线：

```text
LLM 做语义理解、图型选择、模板选择、结构化 Job 填充；
确定性软件做契约校验、排版、渲染、QA 和 manifest 留痕。
```
