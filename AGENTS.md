**始终使用中文与我交流**

# 核心约束清单

> **红线（MUST NOT）**：
> - 未经用户确认，**禁止回滚代码、删除分支**
> - 未经用户允许，**禁止擅自 checkout 任何文件**
> - **禁止直接修改 `node_modules/` 下任何三方依赖的源码**（`pnpm install` 会被覆盖，CI/其他成员环境无法复现）
> - **禁止使用 playwright、chromium 等 Web 自动化测试工具**（开发环境为 WSL，未经用户明确允许，不得调用）

> **计划/报告输出**：
> - 计划文档 → `docs/plans/YYYYMMDD_简要描述.md`
> - 报告文档 → `docs/reports/YYYYMMDD_简要描述.md`

---

## 1. 项目架构

待补充	

## 2. 开发命令

| 命令 | 说明 |
|------|------|
| `pnpm install` | 安装依赖 |
| `npm run dev` | 启动开发服务器 (http://localhost:3000) |
| `npm run build` | 构建生产版本 |
| `npm run lint` | ESLint 检查 |
| `npm run typecheck` | TypeScript 类型检查 |


## 3. 计划与报告

**触发词**：`制定计划`、`生成计划`、`实施计划` → 使用 **analyzing-code-then-planning** skill

**触发词**：`评估`、`审查`、`检查`、`分析`、`review` → 生成报告到 `docs/reports/`

---

## 4. 强制任务

### 实施计划完整性（MUST）

每个实施计划文档开头**必须**包含：
```markdown
---
创建时间: YYYY-MM-DD HH:MM
状态: [待开始|进行中|已完成|已暂停]
---
```

计划执行步骤：
1. 更新设计文档（仅当涉及架构/API/DB变更时）
2. 清理无用、重复代码
3. 执行任务
4. 更新状态为"已完成"

### 状态同步（MUST）

- 开始执行：`待开始` → `进行中`
- 暂停执行：`进行中` → `已暂停`
- 恢复执行：`已暂停` → `进行中`
- 全部完成：`进行中` → `已完成`

### 自我进化（SKILL: proactive-self-improving-agent-v2）

**触发词**：`总结、学习、进化、提交、commit → 使用 **`proactive-self-improving-agent-v2`** skill 自动捕获经验并安全进化。

- 命令失败 → 记录到 ERRORS
- 用户纠正 → 记录到 LEARNINGS
- 任务完成 → 回顾有新经验则记入
- 同一经验 ≥3 次 → 晋升到 AGENTS.md 或 TOOLS.md

---
