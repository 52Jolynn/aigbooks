---
创建时间: 2026-08-03 17:00
状态: 已完成
类型: 风险研究 / 实施前评估
范围: build-image.sh 前端预构建 + dist.tar.gz + Dockerfile COPY 解压 方案
---

# build-image.sh 前端预构建方案 — 风险研究

## 0. 摘要

将 `Dockerfile` 第一阶段 `node:22-bookworm-slim` 内的 `pnpm install`/`pnpm build` 迁移到 `deploy/docker/build-image.sh` 宿主机执行，并把产物 `frontend/dist` 打成 tar.gz 后由 Dockerfile 解压落位。

研究范围仅限**风险识别与实施约束**，不涉及代码改动。

## 1. 现状基线（事实清单）

| 项 | 当前值 | 出处 |
|---|---|---|
| Dockerfile 第一阶段 | `node:22-bookworm-slim`，内嵌 `corepack enable` + `pnpm install --frozen-lockfile` + `pnpm build` | `Dockerfile:1-8` |
| Dockerfile 复制 dist 方式 | `COPY --from=frontend-builder /src/frontend/dist /usr/share/nginx/html`（目录直拷） | `Dockerfile:37` |
| `.dockerignore` | 已排除 `**/dist`、`frontend/dist`、`**/node_modules`、`**/.vite` | `.dockerignore:8-18` |
| `build-image.sh` 内容 | 仅 `docker build --platform ... -f Dockerfile .`，**不参与**前端构建 | `deploy/docker/build-image.sh` |
| `frontend/dist` 体积 | **110 MB**（含 `models/PP-OCRv5_*.tar` 各 ~10MB、`ort-wasm/*.wasm` ~10MB、字体 woff/woff2） | 实际 `du -sh` |
| `frontend/node_modules` 体积 | **517 MB**（pnpm 硬链接 store） | 实际 `du -sh` |
| `package.json#build` | `vue-tsc --noEmit && vite build` | `frontend/package.json:8` |
| 依赖关键包 | `@paddleocr/paddleocr-js` ^0.4.2、`onnxruntime-web` 1.27.0、Vue 3.5、vue-tsc ^2.1.0 | `frontend/package.json:13-36` |
| nginx 前端路由 | `try_files $uri $uri/ /index.html;`（SPA 必须） | `deploy/docker/nginx.conf:37` |
| nginx 反代主机 | 镜像内 sed 改写为 `127.0.0.1:8000`（port 8000） | `Dockerfile:39-40` |
| `entrypoint.sh` | `nginx -t && nginx && exec "$@"`（tini 包装） | `deploy/docker/entrypoint.sh` |
| README 构建说明 | 仅描述 `bash deploy/docker/build-image.sh`、跨架构 `PLATFORM=...` | `deploy/docker/README.md:16-34` |

## 2. 风险清单

> 每条标注**严重度**、**触发场景**、**可参考的历史经验**（doc-id）。

### R1 · `.dockerignore` 仍排除 `frontend/dist`，tar 包进不去构建上下文【严重】

- **触发**：当前 `.dockerignore:8,13,18` 三处排除 dist；若 Dockerfile `COPY frontend-dist.tar.gz`，但该文件被 `.dockerignore` 一并忽略，则 `docker build` 直接失败（`file not found` in build context）。
- **历史经验**：参见 `LRN-20260720-901` (b0b6a1b6) — pre-flight 不验证文件是否真进上下文，类同"假设存在 vs 实际存在"。
- **缓解**：tar 命名不要带 `dist` 字面量（如 `frontend-bundle.tar.gz`）；并在 `build-image.sh` 完成后用 `docker build --no-cache --progress=plain` 的早期阶段日志确认上下文大小变化。

### R2 · vue-tsc 在 AIGBooks 项目存在已知缺陷【严重】

- **触发**：`pnpm build` 等价于 `vue-tsc --noEmit && vite build`。`vue-tsc@2.x` 在 Vue 3.5 + 当前 tsconfig 组合下，`-b`（build-mode）会随机抛 `Cannot find type definition file for 'vue/__globalTypes_3.5_false'`；`--noEmit` 通过。
- **历史经验**：
  - `ERR-20260731-003` (fc0f5f64) — vue-tsc `-b` 随机失败，已建议改 `--noEmit`；当前 `package.json` 已采用 `--noEmit` ✅
  - `ERR-20260716-002` (10e42a73) — `vue-tsc@2.0.0` 入口依赖不完整，需 `pnpm install` 修复；**强制要求宿主 pnpm 与 `pnpm-lock.yaml` 同步**。
- **缓解**：`build-image.sh` 必须用 `pnpm install --frozen-lockfile`（与原 Dockerfile 完全一致语义）；不要临时改 `vue-tsc` 版本。

### R3 · 宿主机构建污染 + 镜像可重复性降低【中】

- **触发**：原本镜像内 `pnpm install` 在 Linux/Bookworm 沙箱内一次性完成，输出对 Node 版本、glibc、CPU 指令集敏感；移到宿主机后，宿主 macOS/Windows/Ubuntu/CentOS/Alpine 各自产出二进制/包内容（如 esbuild 原生包），可能与运行时 nginx 环境不一致。
- **历史经验**：
  - `ERR-20260701-001` (5a224c5d) — 设计文档凭印象声明"已验证"，实际包根本不存在。宿主机构建更容易因依赖缺漏/版本漂移引入隐性差异。
  - `LRN-20260312-002` (889ab861) — 国产驱动/网络受限环境的依赖安装需要"特殊网络"，宿主机构建时同样会撞。
- **缓解**：
  1. 在 `build-image.sh` 顶部强制 Node ≥ 22（与 `node:22-bookworm-slim` 对齐）、pnpm ≥ 9。
  2. 跨架构（`PLATFORM=linux/arm64`）宿主为 amd64 时，构建结果可能仍可用（Vite/Rollup 产物主要是 wasm + JS），但 esbuild 平台二进制需要 `--target`；当前 `vite.config.ts` 未显式 target，需复核。
  3. README 必须明确"宿主需 Node 22 + pnpm 9 + Linux x86_64/aarch64"。

### R4 · `tar` "file changed as we read it" 陷阱【中】

- **触发**：把 `frontend/dist` 打包成 tar.gz 时，若目标 tar 文件本身就在 `frontend/dist/` 内（不该发生）或在 `frontend/` 同级被监听，tar 会报 `file changed as we read it`。
- **历史经验**：`LRN-20260319-001` (4a797adc) — 唯一一条同主题教训，给出标准范式"先在外部创建 → 再 mv 到目标位置"。
- **缓解**：tar 输出路径写**项目根目录**或 `/tmp`，**绝不要**写 `frontend/dist/...`；完成后再 `mv` 到 `deploy/docker/` 之类的固定目录。

### R5 · 构建上下文体积激增【中】

- **触发**：当前 `.dockerignore` 排除 `frontend/dist`（110MB）。方案改造后需要把 dist（或其 tar 包，gzip 后 ~30-50MB）打进构建上下文。若**整目录** COPY 而非 tar，则 dist 内每个文件都成独立层，影响 BuildKit 缓存。
- **历史经验**：未检索到直接条目，但 `LRN-20260718-003` (7691fd49) 提示"接近 100% 不等于实现正确"——容易被"构建跑通"掩盖。
- **缓解**：
  - 用单文件 tar.gz COPY 而非目录 COPY（一个 layer、解压一步完成）。
  - `.dockerignore` **保留** `frontend/dist`、`frontend/node_modules` 排除项，**只新增**白名单允许 tar 文件进入（如 `!deploy/docker/frontend-bundle.tar.gz`）。

### R6 · Dockerfile 失去前端构建阶段后，缓存粒度变粗【低-中】

- **触发**：原本修改 Vue 文件只会重跑 `RUN pnpm build`；改造后**任何**前端改动都需重打 `frontend-bundle.tar.gz` 并重新 `docker build`，无法利用 docker 层的 cache hit。
- **历史经验**：未检索到直接条目，但 `LRN-20260314-005` (1f66dc18) 提示"单文件缓存不足以覆盖构建链"。
- **缓解**：
  - CI 流程应明确"前端 → tar → docker build → push"分阶段缓存（前端缓存 `frontend/node_modules/.pnpm-store`，docker 缓存 layer）。
  - README 增加"增量构建请先跑 `bash deploy/docker/build-image.sh` 重生 tar"提示。

### R7 · docker-compose.yaml 引用路径变更【低】

- **触发**：当前 `docker-compose.yaml` 通过 `Dockerfile` 上下文构建；若 `build-image.sh` 隐含 `frontend-bundle.tar.gz` 存在，compose 的 `build:` 段需要确保依赖关系正确。
- **历史经验**：`err-20260803-001` (6e0c7de1) — Compose V2 vs V1 语法差异。建议至少验证 compose 在不依赖 `build-image.sh` 时的失败信息。
- **缓解**：在 `docker-compose.yaml` 加 `build: { context: ., dockerfile: Dockerfile }`，并在 README 提示 "compose 用户应先执行 build-image.sh"。

### R8 · COOP/COEP 头与 SPA 路由在解压后失效【低】

- **触发**：nginx.conf 包含 `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp`（`nginx.conf:33-34`）以及 `try_files $uri $uri/ /index.html`（`nginx.conf:37`）。若解压后路径布局与原 `COPY` 一致则无影响；一旦解压到中间目录再 `mv` 可能改变文件 inode/权限。
- **历史经验**：`lrn-20260713-001-ort-proxy-worker` (a3c35daf) — 此类头关系到 wasm 是否能跑，必须保留所有 wasm/ort-wasm 模型文件解压后的可访问性。
- **缓解**：解压目标必须**直接**是 `/usr/share/nginx/html`，不能有中间目录；解压后 `RUN find /usr/share/nginx/html -type f | wc -l` 自检体积。

## 3. 注意事项（实施前 checklist）

> 按"双端任务 pre-flight"思路整理（参见 LRN-20260720-901 b0b6a1b6）。

### N1 · 路径与命名约束

- [ ] tar 输出文件名**不含** `dist` / `node_modules` 字样，避免 `.dockerignore` 误杀；建议 `deploy/docker/frontend-bundle.tar.gz`。
- [ ] Dockerfile 中 `ADD frontend-bundle.tar.gz /usr/share/nginx/html/` 或 `COPY ... && RUN tar -xzf ... -C /usr/share/nginx/html/` —— **解压目标就是** nginx 根，避免中间目录。
- [ ] `build-image.sh` 必须 `cd` 到项目根（脚本当前路径默认 `.`，已 OK），不能用相对路径拼 dist。

### N2 · 依赖完整性

- [ ] 宿主机 pnpm 必须与 `frontend/pnpm-lock.yaml` 严格一致（`pnpm install --frozen-lockfile`），与原 Dockerfile 语义对齐。
- [ ] 检查 `corepack enable` 是否已在宿主机执行过；若 pnpm 不是通过 corepack 激活，必须在脚本里显式 `corepack enable`（与 Dockerfile 第 4 行一致）。
- [ ] 跨平台构建（arm64↔amd64）必须验证 esbuild/rollup 原生模块是否需要 `--target` 或运行 `pnpm rebuild`。

### N3 · .dockerignore 调整

- [ ] **保留** `**/dist`、`**/node_modules`、`**/.vite` 排除（避免无意义文件进上下文）。
- [ ] **新增**白名单：`!deploy/docker/frontend-bundle.tar.gz`，确保 tar 文件能进入上下文。
- [ ] 同步更新 `frontend/.gitignore`（无需改，已排除 dist）。

### N4 · 解压层验证

- [ ] 解压后必须存在 `index.html`（nginx 入口），且 `ort-wasm/`、`models/`、`zxing/`、`assets/`、`covers/` 等目录层级与 `dist/` 完全一致。
- [ ] `entrypoint.sh` 的 `nginx -t` 已经覆盖配置正确性，但**不**验证静态文件存在性；建议 `Dockerfile` 增加 `RUN test -f /usr/share/nginx/html/index.html`。
- [ ] `client_max_body_size 512M`（nginx.conf:5）和 `add_header Cross-Origin-*-Policy`（nginx.conf:33-34）在解压后不受影响。

### N5 · 文档同步

- [ ] `deploy/docker/README.md` 第 16-34 行"构建镜像"段需补充前置步骤：`bash deploy/docker/build-image.sh` 实际包含前端构建，需 Node 22 + pnpm 9 环境。
- [ ] 顶层 `README.md` 若引用构建流程，需同步。
- [ ] `docker-compose.yaml` 的 `build:` 段需明确上下文路径，必要时加注释提示"前置依赖 frontend-bundle.tar.gz"。

### N6 · CI/本地构建流程

- [ ] `build-image.sh` 当前用 `docker version --format '{{.Server.Arch}}'` 取架构；保留。
- [ ] `set -euo pipefail` 已启用，新增步骤需继续遵守。
- [ ] 在 `pnpm build` 失败时**不要**继续打包 tar，必须立即 exit 非 0（避免半成品 tar 进入镜像）。
- [ ] 若前端构建产物含敏感信息（如 `.env.local` 被误拷入 dist），`tar` 打包前应 grep 一次 `.env` / `*.key` / `*.pem`。

## 4. 最佳实践建议

### B1 · 把 frontend 构建产物当作"不可变制品"对待

- 在 `deploy/docker/` 下放一个 `frontend-bundle.tar.gz`（git ignore 或 git lfs，按团队约定），**版本号**纳入文件名（如 `frontend-bundle-20260803.tar.gz`）；Dockerfile 通过参数 `--build-arg BUNDLE=...` 接收。
- 历史依据：`LRN-20260720-901` (b0b6a1b6) 强调"产物清单必须明确"，`LRN-20260318-002` (c8bdf868) 提示"添加功能时只关注调用链，忽视数据结构处理逻辑"——同样适用于此处：版本号 = 数据结构指纹。

### B2 · 沿用 `--frozen-lockfile` + `corepack` + Node 22 三件套

- 这是 Dockerfile 已经在用的方案，必须在宿主机脚本里**完全复制**：不引入 npm、不引入 yarn、不引入非锁文件安装。
- 历史依据：`ERR-20260716-002` (10e42a73) — node_modules 不完整会让 build 失败；`ERR-20260726-001` (fafcac18) — 必须用真实 build 脚本而非 tsc 单独跑。

### B3 · 单文件 tar.gz COPY 优于多文件目录 COPY

- 推荐 `COPY deploy/docker/frontend-bundle.tar.gz /tmp/bundle.tar.gz && RUN tar -xzf /tmp/bundle.tar.gz -C /usr/share/nginx/html && rm /tmp/bundle.tar.gz`。
- 历史依据：通用 docker 最佳实践；规避 R5 + R8 双重风险。`ADD` 在某些 Docker 版本会**自动解压**，行为不直观，建议显式 `COPY + RUN tar`。

### B4 · 保留 `frontend-builder` 阶段作为可选 fallback

- 文档化"如宿主机无 Node/pnpm，请回到原始 Dockerfile 多阶段流程"。即 `build-image.sh` 检测 `command -v pnpm || command -v node`，缺失则提示用户。
- 历史依据：`LRN-20260312-002` (889ab861) — 网络/环境受限时的优雅降级思路。

### B5 · 在 Dockerfile 内加入"产物完整性"自检

```dockerfile
RUN test -f /usr/share/nginx/html/index.html \
 && test -d /usr/share/nginx/html/ort-wasm \
 && test -d /usr/share/nginx/html/models \
 && find /usr/share/nginx/html -type f | wc -l
```

- 让镜像构建失败立即可见，而不是运行时 nginx 报 404。
- 历史依据：`LRN-20260718-003` (7691fd49) — "编译通过 ≠ 实现正确"。

### B6 · build-image.sh 输出可观测的产物元信息

```text
[build-image] frontend bundle: 110M → 38M (gzip), 1423 files
[build-image] sha256: xxxxx
[build-image] nginx root layout: index.html, assets/, ort-wasm/, models/, zxing/, covers/
```

- 把 tar 包大小、文件数、sha256、目录结构打印出来。CI 可直接 grep 校验。
- 历史依据：通用 CI 可观测性原则。

### B7 · `.dockerignore` 调整采用白名单 + 注释

修改后的 `.dockerignore` 应如下（**示意**）：

```text
.git
.gitignore
... (保留原排除项)
**/dist
**/node_modules
**/.vite

# === 白名单：仅放行前端预构建产物 ===
!deploy/docker/frontend-bundle.tar.gz
!deploy/docker/frontend-bundle.tar.gz.sha256
```

- 历史依据：`LRN-20260720-901` (b0b6a1b6) — pre-flight 必须确认文件实际进入上下文。

### B8 · 把"前端构建"独立成可选步骤

`build-image.sh` 拆三段（与现有 helpai-hub 风格一致，参见 README 提示 `./docker/scripts/build.sh all`）：

```bash
bash deploy/docker/build-image.sh frontend   # 仅前端 tar
bash deploy/docker/build-image.sh backend    # 仅后端 + nginx 镜像（依赖 tar 已存在）
bash deploy/docker/build-image.sh all        # 串行执行前端 + 镜像
```

- 历史依据：参考 `b8a8a24d-bc82-45b7-aa1b-9be603084795` (README) 已有的多目标构建约定。

## 5. 经验索引（本次研究引用的 memory 条目）

| doc-id | 标题 | 与本次关联点 |
|---|---|---|
| `4a797adc-4db6-4086-9ae2-0d1300d73ae8` | LRN-20260319-001 tar "file changed as we read it" | R4 / N1 — tar 必须在外部创建 |
| `10e42a73-3674-4a6a-8490-888389ac238c` | ERR-20260716-002 vue-tsc 入口依赖不完整 | R2 / B2 — 必须 --frozen-lockfile |
| `fc0f5f64-3b78-428b-800e-3ea4eba95beb` | ERR-20260731-003 vue-tsc -b 随机失败 | R2 — 当前已用 --noEmit，保持 |
| `fafcac18-46f9-4580-8f50-ef7f3c48d11b` | ERR-20260726-001 Vue SFC 类型检查 | N2 — 必须用真实 build 脚本验证 |
| `b0b6a1b6-9497-4862-94cf-8d0e4ecb5f39` | LRN-20260720-901 双端镜像 pre-flight | N1 / B7 — 产物清单与上下文验证 |
| `889ab861-b4cb-433e-91ab-bf2af2d031f7` | LRN-20260312-002 驱动/网络受限降级 | R3 / B4 — 优雅降级思路 |
| `5a224c5d-144c-4d23-b57c-97433f780550` | ERR-20260701-001 设计文档凭印象"已验证" | R3 — 必须验证依赖实际可用 |
| `7691fd49-7787-44cc-8fa7-f42718276902` | LRN-20260718-003 编译通过 ≠ 实现正确 | R5 / B5 — 自检产物完整性 |
| `a3c35daf-3cfe-4df0-96d6-6e5ebdd61088` | lrn-20260713-001 ort-proxy-worker | R8 — wasm/ort-wasm 必须可访问 |
| `1f66dc18-21e6-4d9a-94e6-9e2bac02b640` | LRN-20260314-005 单文件缓存不足 | R6 — 构建缓存粒度提示 |
| `6e0c7de1-7882-40fc-8566-16043e51a1f6` | err-20260803-001 Compose V2/V1 语法 | R7 — compose 流程验证 |
| `c8bdf868-241a-488e-a9dd-5916e28c2d00` | LRN-20260318-002 数据结构 vs 调用链 | B1 — 版本号作为指纹 |
| `b8a8a24d-bc82-45b7-aa1b-9be603084795` | README（helpai-hub 多目标构建） | B8 — 拆 frontend/backend/all |

## 6. 结论与建议顺序

1. **建议推进**：方案整体可行，核心收益是缩短 CI 迭代时间（前端改动无需重建整个 docker 层）。
2. **优先处理 R1、R2、R3**：`.dockerignore` 白名单 + pnpm frozen-lockfile + 跨平台验证是硬阻塞。
3. **次优先 R4、R5、B3**：tar 外部创建 + 单文件 COPY 解压。
4. **可推迟 B1（带版本号文件命名）、B4（fallback 文档）**：作为 v2 增强。
5. **验证门**：实施完成后必须跑通以下端到端检查：
   - `bash deploy/docker/build-image.sh frontend` → 生成 tar + sha256
   - `docker build ... -f Dockerfile .` → 通过，包含前端产物自检
   - `docker compose up -d` → 启动后 `curl -f http://localhost:8080/` 与 `curl -I http://localhost:8080/ort-wasm/ort-wasm-simd-threaded.jsep.wasm` 双 200。

---

**研究范围限定**：本报告未触碰任何源代码或构建脚本；建议在 review 通过后另立实施计划进入开发流程。