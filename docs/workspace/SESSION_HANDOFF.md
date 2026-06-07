# Session Handoff

最后更新：2026-06-07

## 本次完成

- 创建 `docs/workspace/` 项目记忆系统。
- 建立状态、路线图、决策日志、知识地图、维护协议和交接模板。
- 根 `WORKSPACE.md` 已作为项目工作入口。
- `entrypoint/ENTRYPOINT.md` 已改为兼容入口，指向新的项目记忆系统。
- 外层 `bid-tool.code-workspace` 已指向真实项目目录。
- 新增 `docs/PROJECT_STRUCTURE.md`，规定项目目录结构和新增文件归位规则。
- 长期架构文档迁移到 `docs/architecture/illustration-v2/`。
- 配图标准文档迁移到 `docs/standards/illustration/`。

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

## 下一次最小可执行任务

从 `T-002` 或 `T-003` 开始：

- `T-002`：收敛旧版文档指向，避免新开发继续读旧 `illustration/`。
- `T-003`：梳理 `src/bid_tool/illustration_v2/core/decision.py`，让 plan/manifest 显式包含 tier 与降级原因。

推荐先做 `T-003`，因为它直接影响“高质量、稳定、快速、高性价比”的自动配图主线。

## 注意事项

- 当前工作区已有大量未提交改动，不要回滚。
- 旧版 `src/bid_tool/illustration/` 在当前工作区表现为删除迁移。
- 新开发主入口是 `src/bid_tool/illustration_v2/`。
- 示例 Job 可 smoke，但不能代表真实质量。
