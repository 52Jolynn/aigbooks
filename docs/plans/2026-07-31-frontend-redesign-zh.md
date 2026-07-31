---
创建时间: 2026-07-31 15:55
状态: 已完成
---

# AIGBooks · 全站视觉重构与中文化实施计划

> 范围：仅修改 `frontend/`，严格不动 `node_modules/`、`backend/`、`deploy/`、`scripts/`、`docs/plans/`、`docs/reports/`。
> 原则：保留现有 API、路由 `name`、状态管理、组件 Props/Emits 与测试契约；扩展设计 token 与组件层；新增 `src/i18n/zh.ts` 常量作为单一信息源。

---

## 0. 计划概述

- **目标**：将 AIGBooks 全站视觉重构为“临床样本台 / 图书检疫所”风格，并将全部固定界面文案中文化，保留现有 API、业务流程与测试契约。
- **范围**：4 路由 + 13 组件 + 2 store + 1 OCR 工具 + 7 spec 文件 + 1 全局样式表 + `index.html`；新增 `src/i18n/zh.ts` 常量模块。
- **预期成果**：可访问性、对比度、响应式与 reduced-motion 均合规；`pnpm typecheck` / `pnpm test` / `pnpm build` 全部通过；视觉记忆点为“样本袋 + 检验标签 + 等宽编号”。
- **预计工时**：1.5 个工作日（含 1 轮 30 分钟设计对齐已完成）。

---

## 1. 需求背景

- **原始需求**：重新设计本网站，同时站点语言为中文。
- **澄清记录**：范围=全站视觉重构；视觉方向=图书检疫所（冷白 + 检验绿 + 危险橙）；品牌=“AI 图书检疫所”为主名、AIGBooks 为英文副标；动效=克制但鲜明并支持 `prefers-reduced-motion`；文案语气=专业审慎；不伪造“合格/不合格”等业务结论。
- **业务价值**：在不增加后端负担的前提下，提升中文用户的辨识效率、阅读舒适度与站点可信度，并显著降低英文残留对读者的认知摩擦。
- **成功标准**：
  1. 全站任何固定文案均为中文；动态数据（书名 / 作者 / ISBN / 举报描述）保持原样。
  2. 视觉统一冷白 + 检验绿 + 危险橙；状态色同时具备形状 + 字符双编码。
  3. 全部 7 个 spec 通过、`vue-tsc --noEmit` 无报错、`vite build` 成功。
  4. 关键交互（首屏入场、按钮反馈、hover、检验章落印）≤300ms 并具备 reduced-motion 降级。
  5. 任意页面键盘可达，焦点环可见，错误提示不依赖 `alert()`。

---

## 2. 影响范围

### 2.1 预计影响文件

| # | 文件路径 | 变更等级 | 变更性质 |
|---|---|---|---|
| 1 | `frontend/index.html` | LOW | `<title>` 改为中文、补充 meta description/keywords、添加 theme-color |
| 2 | `frontend/src/i18n/zh.ts` | NEW | 新增文案与日期格式化常量（单一信息源） |
| 3 | `frontend/src/styles/dossier.css` | HIGH | 重写为临床样本台视觉系统；保留 BEM 与 `--font-cn` |
| 4 | `frontend/src/main.ts` | NONE | 不动 |
| 5 | `frontend/src/App.vue` | LOW | `<main>` 包裹 RouterView、补充 skip-link |
| 6 | `frontend/src/views/HomeView.vue` | MEDIUM | 文案中文化 + 顶部新增“重要声明”卡片 |
| 7 | `frontend/src/views/SearchView.vue` | MEDIUM | 文案中文化 + 空态分支 |
| 8 | `frontend/src/views/BookDetailView.vue` | HIGH | 报告时间线重构 + 文案中文化 + 警告卡片 |
| 9 | `frontend/src/views/ReportView.vue` | HIGH | 申请单布局 + MARC 字段标签 + FormError 横幅 |
| 10 | `frontend/src/views/__tests__/ReportView.spec.ts` | HIGH | 同步更新断言 |
| 11 | `frontend/src/components/Masthead.vue` | HIGH | 主名 + 副标 + 案号徽章 + 中文日期 |
| 12 | `frontend/src/components/Colophon.vue` | MEDIUM | 文案中文化 |
| 13 | `frontend/src/components/UtilityBar.vue` | MEDIUM | 改为左侧主按钮 + 右侧订阅链接 |
| 14 | `frontend/src/components/SectionHeader.vue` | NONE | 仅依赖 props |
| 15 | `frontend/src/components/Stamp.vue` | LOW | slot 默认文案 + 类名扩展 |
| 16 | `frontend/src/components/FeaturedReport.vue` | HIGH | 样本袋布局 + 文案中文化 |
| 17 | `frontend/src/components/ReportCard.vue` | HIGH | 样本袋布局 + 文案中文化 |
| 18 | `frontend/src/components/ReportsGrid.vue` | LOW | 网格参数微调 |
| 19 | `frontend/src/components/SearchBox.vue` | MEDIUM | “图书检索”贴纸样式 + aria-label |
| 20 | `frontend/src/components/FormField.vue` | MEDIUM | `aria-invalid` / `aria-describedby` 绑定 |
| 21 | `frontend/src/components/FileUploader.vue` | MEDIUM | 改为 `<button>` 触发 + `aria-label` |
| 22 | `frontend/src/components/VoteButton.vue` | LOW | aria-label 中文化 |
| 23 | `frontend/src/components/EvidenceList.vue` | LOW | alt 用文件名而非 MIME |
| 24 | `frontend/src/components/__tests__/ReportCard.spec.ts` | MEDIUM | mock 数据不变，断言改为 `toContain('ISBN')` 等 |
| 25 | `frontend/src/components/__tests__/Stamp.spec.ts` | MEDIUM | 默认 slot 文案同步 |
| 26 | `frontend/src/components/__tests__/SearchBox.spec.ts` | LOW | 仅在 placeholder 改变时同步 |
| 27 | `frontend/src/components/__tests__/FormField.spec.ts` | NONE | prop 文本不变 |
| 28 | `frontend/src/components/__tests__/FileUploader.spec.ts` | NONE | prop 文本不变 |
| 29 | `frontend/src/components/__tests__/VoteButton.spec.ts` | NONE | mock 数据不变 |
| 30 | `frontend/src/ocr/__tests__/index.spec.ts` | NONE | 不动 |
| 31 | `frontend/src/ocr/index.ts` | LOW | console.warn 文案中文化 |
| 32 | `frontend/src/stores/reports.ts` | LOW | console.warn 文案中文化 |
| 33 | `frontend/src/stores/fingerprint.ts` | NONE | 不动 |
| 34 | `frontend/src/api/index.ts` | LOW | console.warn 文案中文化 |
| 35 | `frontend/src/api/{books,search,reports}.ts` | NONE | 不动 |
| 36 | `frontend/src/utils/fingerprint.ts` | NONE | 不动 |
| 37 | `frontend/src/router/index.ts` | NONE | name 不动 |
| 38 | `frontend/package.json` | NONE | 不引入新依赖 |
| 39 | `frontend/vite.config.ts` / `vitest.config.ts` / `tsconfig*.json` | NONE | 不动 |

合计：~32 个文件新增/修改。

### 2.2 数据库与依赖

- **数据库变更**：无。
- **第三方依赖**：无新增（保持 YAGNI；不使用 i18n 框架）。

---

## 3. 设计原则遵循

基于代码调查结论，新代码遵循以下项目原则：

1. **组合式 API + TS 严格模式**：所有 `.vue` 维持 `<script setup lang="ts">`，禁止新增未用 props/import。
2. **CSS 变量驱动**：所有色值、字号、间距集中在 `:root`，不散落到组件。
3. **BEM + 状态类**：保留 `.block__element` 与 `.is-*` 命名，新增 `.quarantine-*` 与 `.sample-*` 命名空间。
4. **响应式断点**：沿用 900px / 600px 节点，新增 1024px 节点以区分桌面网格。
5. **可访问性底线**：键盘可达 + 焦点环可见 + `prefers-reduced-motion` 降级 + 错误不依赖 `alert()`。
6. **文案单一信息源**：所有固定中文文案来自 `src/i18n/zh.ts`；测试与组件同步引用。
7. **不伪造业务结论**：状态标签仅反映真实数据（举报数、证据数、时间、票数）；必要时显示“风险较为集中”提示。

---

## 4. 任务分解

### 任务 1：基础设施与文案常量 [P0, 0.25 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 新增 | `frontend/src/i18n/zh.ts` | 中文文案 + 相对时间/日期格式化函数 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 新增 | `zh.ts` 常量 | `siteTitle / siteSubtitle / navItems / home / search / report / detail / button / status / disclaimer / error / time` |
| 新增 | `zh.ts` 函数 | `formatRelative(zh, date)`、`formatDate(zh, date)`、`formatCaseNumber(zh, id, date)` |

#### 测试用例
| ID | 场景 | 输入 | 预期 | 方法 |
|---|---|---|---|---|
| TC-1.1 | 相对时间 | `Date.now()` / `Date.now() - 3h` / `Date.now() - 2d` | `刚刚` / `3 小时前` / `2 天前` | 单元测试 |

#### 设计要点
- 时间格式化统一在 `zh.ts`，组件只引用，不重复实现。
- 文案常量导出为 `as const`，便于类型推断。

---

### 任务 2：全局样式与设计 Token [P0, 0.5 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 重写 | `frontend/src/styles/dossier.css` | 重构为临床样本台视觉系统 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 重写 | `:root` | 全面替换 token：surface / ink / quarantine-ok / warn / alert / mono |
| 重写 | `body::before` | 冷白磨砂纸纹理（透明度 ≤4%） |
| 新增 | `.sample-bag` / `.quarantine-*` / `.disclaimer-*` | 样本袋、状态标签、声明卡片 |
| 新增 | `.focus-visible` | 全局焦点环 |
| 新增 | `@media (prefers-reduced-motion: reduce)` | 全局动效降级 |
| 保留 | `.stamp--featured` / `.stamp--mini` | 类名不变以兼容测试 |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-2.1 | 视觉对比度 | `--ink-deep` 在 `--surface` 上 ≥7.0，`--quarantine-warn` ≥4.5 |
| TC-2.2 | reduced-motion | `@media` 块存在并对 `.reports-grid > *` / `.featured` / `.stamp--pulse` 应用 |

#### 设计要点
- token 命名按语义角色，不使用具体色名（避免 `.green-500`）。
- `--font-cn` 沿用作为中文正文族，新增强化的 `--font-cn-display` 用于样本袋大标题。

---

### 任务 3：全局容器与导航 [P0, 0.25 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/index.html` | `<title>`、meta description、theme-color |
| 修改 | `frontend/src/App.vue` | skip-link、`<main>` 包裹、`<header>` 语义 |
| 修改 | `frontend/src/components/Masthead.vue` | 主名 + 副标 + 案号徽章 + 中文日期 |
| 修改 | `frontend/src/components/UtilityBar.vue` | 改为左侧主按钮 + 右侧订阅链接 |
| 修改 | `frontend/src/components/Colophon.vue` | 中文文案 |
| 修改 | `frontend/src/api/index.ts` | console 文案中文化 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 新增 | `Masthead.vue` | `<header role="banner">`、案号徽章、aria-label |
| 修改 | `Masthead.vue` | 顶部栏日期改为 `formatDate(zh, new Date())` |
| 修改 | `UtilityBar.vue` | DOM 结构改为 `<nav aria-label="快捷操作">` |
| 修改 | `Colophon.vue` | 中文段落 |
| 新增 | `App.vue` | `<a href="#main" class="skip-link">跳到主要内容</a>` |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-3.1 | skip-link 可见性 | `Tab` 首焦点显示 |
| TC-3.2 | 导航语义 | `<nav aria-label="主导航">` / `<nav aria-label="快捷操作">` 存在 |

#### 设计要点
- 顶部栏保留旧的 3 段横排（卷期/栏目名/日期），但全部中文。
- 主标题区使用 `font-family: var(--font-cn-display)`，字号与行高按字阶 H1 处理。

---

### 任务 4：首页 `HomeView` [P0, 0.25 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/src/views/HomeView.vue` | 文案中文化 + 顶部声明卡片 |
| 修改 | `frontend/src/components/FeaturedReport.vue` | 样本袋布局 + 文案 |
| 修改 | `frontend/src/components/ReportCard.vue` | 样本袋布局 + 文案 |
| 修改 | `frontend/src/components/ReportsGrid.vue` | 网格参数微调 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 新增 | `HomeView.vue` 顶部 | `<DisclaimerCard>` 组件 |
| 修改 | `HomeView.vue` | SectionHeader num/title/meta 改中文 |
| 重写 | `FeaturedReport.vue` | 样本袋：封面 + 四角标签 + 描述 + 检验章 |
| 重写 | `ReportCard.vue` | 样本袋：封面 + 案号 + ISBN + 提交时间 + 票数 |
| 重写 | `ReportsGrid.vue` | 桌面 3 列 / 平板 2 列 / 移动 1 列 |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-4.1 | Featured 文案 | `wrapper.text()` 包含 `提交于`、`已收到` |
| TC-4.2 | Card 角标 | DOM 包含 `.sample-bag` 与 `.quarantine-stamp` |

#### 设计要点
- 样本袋使用 1px 边框 + 4px 内阴影模拟透明磨砂；不引入 backdrop-filter。
- 标签采用 `font-family: var(--font-mono)`，颜色统一 `--ink-deep` 或 `--quarantine-warn`。

---

### 任务 5：搜索页 `SearchView` [P0, 0.15 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/src/views/SearchView.vue` | 文案中文化 + 空态分支 |
| 修改 | `frontend/src/components/SearchBox.vue` | “图书检索”贴纸 + aria-label |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 修改 | `SearchBox.vue` | `<span>` 改 `<label for>` + aria-label |
| 修改 | `SearchView.vue` | SectionHeader + 空态分支 |
| 修改 | `SearchView.vue` | placeholder 文案 |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-5.1 | 路由跳转 | `push({ name: 'search', query: { q } })` 仍生效 |
| TC-5.2 | 输入框语义 | `<label>` 与 `<input>` 关联 |

#### 设计要点
- placeholder 默认值改中文；测试断言不依赖 placeholder，因此不破测试。

---

### 任务 6：详情页 `BookDetailView` [P0, 0.5 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/src/views/BookDetailView.vue` | 报告时间线 + 警告卡片 + 文案中文化 |
| 修改 | `frontend/src/components/VoteButton.vue` | aria-label 中文化 + console 文案 |
| 修改 | `frontend/src/components/EvidenceList.vue` | alt 用文件名 |
| 修改 | `frontend/src/stores/reports.ts` | console 文案中文化 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 重写 | `BookDetailView.vue` | 左封面样本袋 + 右报告时间线 |
| 新增 | `BookDetailView.vue` | “风险较为集中”提示（票数差 ≥5 且 ≥3 票时显示） |
| 修改 | `EvidenceList.vue` | `:alt="ev.file_path ?? '证据材料'"` |
| 修改 | `VoteButton.vue` | aria-label 与 console 文案 |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-6.1 | 详情页加载 | `wrapper.text()` 包含 `提交于`、`最早举报于` |
| TC-6.2 | 票数差提示 | mock upvote=6 downvote=0 时显示警告 |
| TC-6.3 | 证据 alt | DOM `<img alt="evidence/xxx.jpg">` |

#### 设计要点
- 报告时间线为垂直列表，每条举报一个 `<li>`，案号 + ISO 时间 + 票数 + 描述 + 证据缩略图。
- 不显示虚构的“合格/不合格”结论。

---

### 任务 7：举报页 `ReportView` [P0, 0.5 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/src/views/ReportView.vue` | 申请单布局 + MARC 字段标签 + FormError 横幅 |
| 修改 | `frontend/src/components/FormField.vue` | `aria-invalid` / `aria-describedby` |
| 修改 | `frontend/src/components/FileUploader.vue` | `<button>` 触发 + aria-label |
| 修改 | `frontend/src/ocr/index.ts` | console 文案中文化 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 重写 | `ReportView.vue` | 三段 `<section>`：OCR、书籍信息、附件 |
| 新增 | `ReportView.vue` | `FormError` 横幅替代 `alert()` |
| 修改 | `FormField.vue` | input/textarea 绑定 `aria-invalid` 与 `aria-describedby` |
| 修改 | `FileUploader.vue` | 触发元素改为 `<button>` + 移除按钮 aria-label |
| 修改 | `ReportView.vue` | 字段标签改 MARC：`020 ISBN / 245 题名 / 100 作者 / 520 摘要` |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-7.1 | 章节标题 | `wrapper.text()` 包含 `OCR` / `书籍信息` / `附件` / `提交举报` |
| TC-7.2 | aria 绑定 | input 含 `aria-invalid="false"` 与 `aria-describedby="form-field-ISBN-error"` |
| TC-7.3 | 错误提示 | 提交空表单显示 banner，不触发 `alert()` |

#### 设计要点
- MARC 字段名作为小标签保持档案感；字段值仍使用中文 placeholder。
- 不引入 Naive UI，保持 `package.json` 不变。

---

### 任务 8：测试同步与验证 [P0, 0.25 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/src/views/__tests__/ReportView.spec.ts` | 文案断言同步 |
| 修改 | `frontend/src/components/__tests__/Stamp.spec.ts` | 默认 slot 文案同步 |
| 修改 | `frontend/src/components/__tests__/ReportCard.spec.ts` | 断言改为包含中文案号/ISBN |
| 修改 | `frontend/src/components/__tests__/SearchBox.spec.ts` | 仅在 placeholder 改变时同步 |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 修改 | `ReportView.spec.ts` | `toContain('OCR')` → `toContain('OCR 扫描')`；同步 Metadata / Attachments / FILE REPORT |
| 修改 | `Stamp.spec.ts` | 默认 slot `` `× ${count}` `` 改为 `` `已收到 × ${count}` `` |
| 修改 | `ReportCard.spec.ts` | 断言添加对“已收到”、“提交于”的子串匹配 |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-8.1 | 全部 7 spec 通过 | `pnpm test` 退出码 0 |
| TC-8.2 | 类型检查通过 | `pnpm typecheck` 退出码 0 |
| TC-8.3 | 生产构建通过 | `pnpm build` 退出码 0 |
| TC-8.4 | dev server 启动 | `pnpm dev` 无报错（手工核对首屏） |

---

### 任务 9：可访问性与响应式收尾 [P0, 0.15 天]

#### 文件调整清单
| 操作 | 文件路径 | 说明 |
|---|---|---|
| 修改 | `frontend/src/styles/dossier.css` | 焦点环 + reduced-motion |
| 修改 | 各 view 根元素 | `<main tabindex="-1">` + 路由切换后 `el.focus()` |

#### 代码调整清单
| 操作 | 位置 | 说明 |
|---|---|---|
| 新增 | `dossier.css` | `*:focus-visible { outline: 2px solid var(--quarantine-ok); outline-offset: 2px; }` |
| 新增 | `dossier.css` | `@media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation-duration: 0.08s !important; transition-duration: 0.08s !important; } }` |
| 修改 | `router/index.ts` 或 `App.vue` | 路由后 `nextTick` 触发 `<main>` 聚焦 |

#### 测试用例
| ID | 场景 | 检查 |
|---|---|---|
| TC-9.1 | 键盘可达 | `Tab` 顺序合理 |
| TC-9.2 | 移动端 | 360px 宽度不溢出 |

---

## 5. 测试计划

| 类型 | 范围 | 验收标准 |
|---|---|---|
| 单元测试 | 7 spec 文件 + i18n 函数 | `pnpm test` 全部通过 |
| 类型检查 | `vue-tsc --noEmit` | 退出码 0，无 TS 报错 |
| 构建 | `vite build` | 退出码 0 |
| 视觉 | 桌面 1440 / 平板 1024 / 移动 360 | 三档断点布局正常 |
| 可访问性 | 键盘 + 屏幕阅读器 | skip-link、aria-label、aria-describedby 完整 |
| 动效 | reduced-motion on/off | 关闭时长 ≤80ms；无位移与旋转 |
| 错误流 | 提交空表单 / 网络 429 | 不调用 `alert()`，显示 banner |

---

## 6. 风险与应对

| # | 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|---|
| R1 | 测试断言遗漏导致 CI 失败 | 高 | 高 | 任务 8 单独列出，逐 spec 核对 |
| R2 | MARC 字段标签造成中文阅读摩擦 | 中 | 中 | 保留中文 placeholder；MARC 字段名做小标签而非主标签 |
| R3 | 样本袋透明效果在低端设备卡顿 | 低 | 中 | 不使用 backdrop-filter；阴影模拟 |
| R4 | 大量绝对路径背景图导致体积上升 | 低 | 中 | 全部 SVG 内联；体积 < 8KB/页 |
| R5 | i18n 常量未来扩展困难 | 低 | 低 | 用 `as const` 导出，便于迁移 vue-i18n |
| R6 | 字体未加载导致中文回退 | 中 | 中 | 保留现有 Fontsource 加载，新增思源黑体（已有 `--font-cn-display`） |
| R7 | 时间格式化在不同浏览器输出差异 | 中 | 中 | 统一使用 `Intl.DateTimeFormat('zh-CN', ...)` + 自定义兜底 |
| R8 | 用户报告单条建议过于敏感 | 低 | 中 | 阈值调高（票数差 ≥5 且 ≥3 票），并在文案明确“建议多方核实” |

---

## 7. 严禁修改项

- `frontend/node_modules/` 任何文件
- `frontend/pnpm-lock.yaml`
- `backend/`、`deploy/`、`scripts/` 全部
- 数据库 migration / 后端 ORM / RSS 输出
- 路由 `name` (`home / search / book-detail / report`)
- `package.json` scripts（不引入 lint 与新依赖）
- `docs/plans/`、`docs/reports/`（新增 plan 文档除外；已存在的调研报告不动）
- `.git/`、`.venv/`、`.ruff_cache/` 等缓存

---

## 8. 验证执行步骤

1. 任务 1：新增 `zh.ts` 与基础单元测试。
2. 任务 2：重写 `dossier.css`，逐步迁移现有类名。
3. 任务 3–7：组件与视图分批改造；每完成一批跑一次 `pnpm test` + `pnpm typecheck`。
4. 任务 8：同步更新测试断言。
5. 任务 9：可访问性收尾。
6. 最终：`pnpm test` → `pnpm typecheck` → `pnpm build` → `pnpm dev` 手工核对 4 路由视觉。