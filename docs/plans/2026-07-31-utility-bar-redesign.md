---
创建时间: 2026-07-31 17:10
状态: 已完成
---

# 顶部 Header 分层 — UtilityBar 重构

## 目标

将快捷操作区从**右下角浮动**迁移到**顶部 Header 分层放置**，消除主导航中"提交举报"和"RSS"与底部 UtilityBar 的重复，建立清晰的视觉层级（核心操作 vs 辅助操作）。

## 改动清单

### 1. `frontend/src/components/Masthead.vue`

**`masthead__top` 改造**（顶部信息行）：
- 在右侧新增 `<div class="masthead__actions">` 容器
- 包含两个元素：
  - RSS 订阅：小尺寸文字链接（次要层级）
  - 提交举报：实心强调色主按钮（核心 CTA）

**`masthead__nav` 清理**：
- 移除 `nav.submit`（提交举报）— 已上移
- 移除 `nav.rss`（RSS 订阅）— 已上移
- 仅保留 `nav.latest`（最新）和 `nav.search`（检索）

### 2. `frontend/src/styles/dossier.css`

**新增样式**（在 `.masthead__nav` 之前）：
- `.masthead__actions` — flex 容器，右对齐，gap 12px
- `.masthead__rss` — 小尺寸 mono 字体链接，灰色，hover 变色
- `.masthead__cta` — 实心强调色按钮（参考现有 `.utility__btn` 视觉变量：`--quarantine-ok` 主色 + `--ink-deep` hover）

**响应式**（追加到文件末尾 mobile 媒体查询）：
- 移动端 `.masthead__top` 改为 `flex-wrap: wrap`
- `.masthead__actions` 占满一行宽度

### 3. `frontend/src/App.vue`

- 删除 `import UtilityBar from '@/components/UtilityBar.vue'`
- 删除 `<UtilityBar />` 节点

### 4. 删除文件

- `frontend/src/components/UtilityBar.vue`（已无引用）

## 验收标准

1. 顶部 Header 第一行可见「RSS 订阅」链接 + 「＋ 提交举报」主按钮
2. 主导航仅保留「最新」「检索」两个浏览型链接
3. 右下角不再有浮动按钮
4. `pnpm typecheck` 通过
5. `pnpm lint` 通过
6. `pnpm build` 通过