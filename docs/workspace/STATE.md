# Current State

最后更新：2026-06-07

## 项目位置

```text
D:\AI_native_change\bid-tool
```

外层工作空间文件：

```text
C:\Users\杨辉\Documents\自动标书项目\bid-tool.code-workspace
```

## 当前目标

围绕标书自动生成项目，持续建设一个高质量、稳定、快速、高性价比的自动配图能力。

当前核心判断：

```text
LLM 负责语义理解、图型选择、模板选择、结构化 Job 填充。
确定性软件负责契约校验、排版、渲染、几何 QA、manifest 留痕。
```

## 当前工作区事实

- Git 分支：`main...origin/main`
- 工作区已有大量未提交改动。
- 旧版 `src/bid_tool/illustration/` 已在工作区表现为删除迁移。
- 当前活跃实现集中在 `src/bid_tool/illustration_v2/`。
- 本轮新增项目记忆系统目录：`docs/workspace/`。
- 本轮新增根入口：`WORKSPACE.md`。
- 本轮新增项目结构说明：`docs/PROJECT_STRUCTURE.md`。
- 长期架构文档已从 `src/bid_tool/devlop-plan/` 迁移到 `docs/architecture/illustration-v2/`。
- 配图内容标准已从 `src/bid_tool/illustration_v2/` 迁移到 `docs/standards/illustration/`。

重要提醒：不要回滚现有未提交改动。任何新修改都要先用 `git status --short --branch` 确认边界。

## 已验证基线

2026-06-07 验证：

```powershell
python -m pytest
```

结果：

```text
57 passed
```

2026-06-07 文件结构整理后复验：

```text
57 passed
```

2026-06-07 配图 smoke：

```powershell
python -m bid_tool.illustration_v2.toolkit --job "examples\示例_配图平台v2任务.json" --output "output\workspace_smoke" --png
```

结果：

```text
rendered 4 asset(s)
```

观察：

- `overall_architecture` 当前走 `structured_svg_fallback`。
- `coverage_trend`、`implementation_gantt`、`risk_matrix` 当前走 `free_svg_floor`。
- 这说明主链路可运行，但模板命中率和决策层能力仍是下一阶段重点。
- 临时输出 `output\workspace_smoke` 已清理。
- 文件结构整理后再次运行同一 smoke，结果正常，临时输出已清理。

## 当前关键风险

1. 既有未提交改动较多，后续开发容易混入无关修改。
2. 旧文档中仍有指向旧版 `illustration/` 的内容，需要逐步收敛到 `illustration_v2/`。
3. 示例 Job 多数图仍走 fallback，说明高质量 Tier 1 模板覆盖不足。
4. 当前“成功”主要由结构校验和渲染完成定义，几何级 QA 仍需要加强。
5. S5 侧 prompt、Schema、能力目录之间可能存在版本漂移。

## 当前推荐下一步

1. 更新 S5 prompt 与 `AI_ILLUSTRATION_API_V2.md`，确保只依赖当前 `illustration_v2` 能力目录。
2. 梳理 `src/bid_tool/illustration_v2/core/decision.py`，明确 Tier、降级链、manifest 字段。
3. 建立真实样本基准集，覆盖至少 5 个高频标书图型。
4. 为模板 SVG 加最小几何 QA：文本 fit、重叠、PNG 可读性。
5. 把每次配图质量问题沉淀为 fixture，避免只修单张图。

## 新会话启动检查

```powershell
cd D:\AI_native_change\bid-tool
git status --short --branch
Get-Content WORKSPACE.md -TotalCount 220
Get-Content docs\workspace\STATE.md -TotalCount 220
Get-Content docs\workspace\ROADMAP.md -TotalCount 260
Get-Content docs\PROJECT_STRUCTURE.md -TotalCount 260
```

如果要改配图相关代码，再读：

```powershell
Get-Content docs\workspace\KNOWLEDGE_MAP.md -TotalCount 260
Get-Content docs\workspace\DECISION_LOG.md -TotalCount 260
```
