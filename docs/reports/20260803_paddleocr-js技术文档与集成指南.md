---
创建时间: 2026-08-03 16:00
状态: 已完成
调研对象: @paddleocr/paddleocr-js
调研目的: 技术文档与集成方案
调研来源: PaddlePaddle/PaddleOCR 官方仓库 (github.com/PaddlePaddle/PaddleOCR/tree/main/paddleocr-js) + npm 官方页面
---

# `@paddleocr/paddleocr-js` 技术文档与集成指南

## 0. 关键结论（先看这个）

- **包身份**：`@paddleocr/paddleocr-js` 是 **PaddlePaddle 官方** SDK（[GitHub](https://github.com/PaddlePaddle/PaddleOCR/tree/main/paddleocr-js)）；npm 上另有一个**同名不同包**的社区版 `paddleocr-js`（Agions 维护，周下载 53，**API 完全不同**，不要混用）
- **当前版本**：v0.4.2（npm 周下载 4,003）
- **核心定位**：浏览器端 PP-OCR 推理 SDK；内置 OpenCV.js + ONNX Runtime Web；支持 WASM 与 WebGPU 两种 backend
- **支持本地模型路径**：✅（任意 `fetch()` 可解析的 URL 都行，包括相对路径 `/models/xxx.tar`，项目当前已经在用此模式）

---

## 1. 仓库与文档入口

| 类别 | 链接 |
|------|------|
| npm 包 | https://www.npmjs.com/package/@paddleocr/paddleocr-js |
| 源码仓库 | https://github.com/PaddlePaddle/PaddleOCR/tree/main/paddleocr-js |
| 核心包目录 | `paddleocr-js/packages/core/` |
| Demo 应用 | `paddleocr-js/apps/demo/` |
| SDK README（EN） | https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr-js/packages/core/README.md |
| SDK README（中） | https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr-js/packages/core/README_cn.md |
| 架构文档 | `paddleocr-js/docs/architecture.md` / `_cn.md` |
| 开发指南 | `paddleocr-js/docs/development.md` / `_cn.md` |
| Monorepo 约定 | `paddleocr-js/docs/monorepo.md` / `_cn.md` |

---

## 2. 安装与版本

```bash
npm install @paddleocr/paddleocr-js
# 或
pnpm add @paddleocr/paddleocr-js
```

当前项目（`frontend/package.json:13`）已锁定 `^0.4.2`，无需改动。

---

## 3. 顶层 API（速查）

```ts
import { PaddleOCR } from '@paddleocr/paddleocr-js';

const ocr = await PaddleOCR.create({
  lang: 'ch',                    // 识别语言
  ocrVersion: 'PP-OCRv5',        // 模型版本
  worker: false,                 // 是否运行在 Worker 中
  ortOptions: {
    backend: 'wasm',             // 'wasm' | 'webgpu' | 'auto'
    wasmPaths: '/ort-wasm/',     // ONNX Runtime Web 的 wasm 资源路径
    numThreads: 2,
    simd: true
  },
  textDetectionModelName: 'PP-OCRv5_mobile_det',
  textDetectionModelAsset: { url: '/models/PP-OCRv5_mobile_det.tar' },
  textRecognitionModelName: 'PP-OCRv5_mobile_rec',
  textRecognitionModelAsset: { url: '/models/PP-OCRv5_mobile_rec.tar' }
});

// 单图或批量，返回 OcrResult[]
const [result] = await ocr.predict(blob);
console.log(result.items);

// 释放
await ocr.dispose();
```

完整 API 列表（来源 `packages/core/src/pipelines/ocr/index.ts`）：

| 方法/对象 | 说明 |
|-----------|------|
| `PaddleOCR.create(options)` | 静态工厂，自动初始化，返回 `PaddleOCR` 或 `WorkerBackedPaddleOCR` |
| `ocr.initialize()` | 异步初始化；返回 `InitializationSummary`（含 backend / provider / 资源摘要 / 耗时） |
| `ocr.getInitializationSummary()` | 获取上一次初始化的摘要 |
| `ocr.predict(image \| images[], params?)` | 预测，返回 `Promise<OcrResult[]>` |
| `ocr.dispose()` | 释放 ONNX 会话 + OpenCV Mat |
| `parseOcrPipelineConfigText(text)` | 解析 YAML 产线配置文本 |
| `normalizeOcrPipelineConfig(config)` | 归一化产线配置 |
| `OcrVisualizer`（`@paddleocr/paddleocr-js/viz`） | 可视化器（左侧原图+检测框，右侧识别文本） |
| `renderOcrToBlob`（viz 子路径） | 一次性便捷渲染函数 |
| `deterministicColor`（viz 子路径） | 索引→稳定 RGB 颜色 |

---

## 4. 关键类型定义（来自 `packages/core/src/index.ts` 导出列表）

```ts
// 运行时参数（同时接受 camelCase 和 snake_case 命名）
interface OcrRuntimeParamsInput {
  text_det_limit_side_len?: number;
  textDetLimitSideLen?: number;
  text_det_limit_type?: 'min' | 'max';
  textDetLimitType?: 'min' | 'max';
  text_det_max_side_limit?: number;
  textDetMaxSideLimit?: number;
  text_det_thresh?: number;
  textDetThresh?: number;
  text_det_box_thresh?: number;
  textDetBoxThresh?: number;
  text_det_unclip_ratio?: number;
  textDetUnclipRatio?: number;
  text_rec_score_thresh?: number;
  textRecScoreThresh?: number;
}

// 单图识别结果
interface OcrResult {
  image: { width: number; height: number };
  items: OcrResultItem[];        // 每条识别行
  metrics: OcrResultMetrics;     // 耗时统计
  runtime: OcrResultRuntime;     // backend / provider 元信息
}

interface OcrResultItem {
  poly: Point2D[];               // 多边形顶点
  text: string;                  // 识别文本
  score: number;                 // 置信度 [0,1]
}

interface OcrResultMetrics {
  detMs: number;                 // 检测阶段耗时（整次 predict 调用）
  recMs: number;                 // 识别阶段耗时（整次 predict 调用）
  totalMs: number;               // 总耗时
  detectedBoxes: number;         // 本图检测框数
  recognizedCount: number;       // 本图识别行数（低于 scoreThresh 被过滤）
}

interface OcrResultRuntime {
  requestedBackend: string;      // 'wasm' | 'webgpu' | 'auto'
  detProvider: string;           // 实际使用的 EP，如 'wasm' / 'webgpu'
  recProvider: string;
  webgpuAvailable: boolean;      // 浏览器是否支持 WebGPU
}

// 创建选项（重要别名）
interface PaddleOCRCreateOptions {
  worker?: boolean | { createWorker?: () => Worker };
  fetch?: typeof fetch;          // 注：worker 模式下不支持自定义 fetch
  initialize?: boolean;          // 是否自动初始化，默认 true
  ortOptions?: OrtOptions;

  pipelineConfig?: unknown;      // YAML 文本或对象；与直接参数冲突时直接参数优先
  unsupportedBehavior?: 'warn' | 'ignore' | 'error';

  lang?: string;
  ocrVersion?: string;
  ocr_version?: string;          // snake_case 别名

  textDetectionModelName?: string;
  text_detection_model_name?: string;
  textRecognitionModelName?: string;
  text_recognition_model_name?: string;

  textDetectionModelAsset?: ModelAsset;     // { url: string }
  textDetectionModelDir?: ModelAsset;
  text_detection_model_dir?: ModelAsset;
  textRecognitionModelAsset?: ModelAsset;
  textRecognitionModelDir?: ModelAsset;
  text_recognition_model_dir?: ModelAsset;

  textDetectionBatchSize?: number;
  text_detection_batch_size?: number;
  textRecognitionBatchSize?: number;
  text_recognition_batch_size?: number;
  batch_size?: number;                       // pipeline 级 batch

  // 还接受所有 OcrRuntimeParamsInput 字段
  // 还接受 [key: string]: unknown（任意扩展）
}

interface ModelAsset {
  url: string;
}

// 初始化摘要
interface InitializationSummary {
  backend: string;
  webgpuAvailable: boolean;
  detProvider: string;
  recProvider: string;
  assets: ModelLoadSummary[];     // 每个资源一个摘要
  elapsedMs: number;
  pipelineConfigWarnings: string[];
}

// ONNX Runtime 配置
interface OrtOptions {
  backend?: 'webgpu' | 'wasm' | 'auto' | (string & {});
  wasmPaths?: string;
  numThreads?: number;
  simd?: boolean;
  proxy?: boolean;                // ORT wasm proxy（worker 模式下被强制关闭）
  disableWasmProxy?: boolean;
}

// 支持的图像输入
type ImageSource = ImageBitmap | Blob | HTMLCanvasElement | ImageData | HTMLImageElement;
// 注意：cv.Mat 仅在主线程模式支持（worker 模式不可传输）
```

---

## 5. 模型加载机制（关键）

### 5.1 入口与归一化

`packages/core/src/resources/model-asset.ts` 定义 `ModelAsset = { url: string }` 与默认资源映射：

```ts
export const DEFAULT_MODEL_ASSETS = {
  'PP-OCRv5_mobile_det': { url: 'https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_mobile_det_onnx_infer.tar' },
  'PP-OCRv5_mobile_rec': { url: 'https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_mobile_rec_onnx_infer.tar' },
  'PP-OCRv6_small_det': { url: '...PP-OCRv6_small_det_onnx_infer.tar' },
  'PP-OCRv6_small_rec': { url: '...PP-OCRv6_small_rec_onnx_infer.tar' },
  'PP-OCRv6_tiny_det':  { url: '...PP-OCRv6_tiny_det_onnx_infer.tar' },
  'PP-OCRv6_tiny_rec':  { url: '...PP-OCRv6_tiny_rec_onnx_infer.tar' }
};
```

### 5.2 模型归档格式约束（**重要**，来自 README + `assertModelResourceSlot`）

| 项 | 要求 |
|----|------|
| 压缩格式 | **未压缩的标准 ustar `.tar`**（SDK 按字节解析，**不解压 gzip**，`.tar.gz` 会失败） |
| 包内必含 | `inference.onnx` + `inference.yml`（可在子目录，按 basename 匹配） |
| `inference.yml` | 必须定义 `model_name`，且必须与 `textDetectionModelName` / `textRecognitionModelName` **完全一致**（`validateLoadedModelName` 强制校验） |
| 失败行为 | 在 `initialize()` 阶段抛 `Error`（HTTP 404、缺条目、空资源、`model_name` 不匹配等），**不静默回退** |

### 5.3 URL 支持范围

- ✅ 相对路径 `/models/xxx.tar`（项目当前用法）
- ✅ 站点根绝对路径 `https://your-domain.com/models/xxx.tar`
- ✅ `blob:` URL（运行时动态生成）
- ✅ `data:` URL（小模型可内联）
- ⚠️ `file://` —— 浏览器安全策略通常禁止（且 `ensureServedFromHttp()` 在 `file:` 协议下会主动抛错）
- ✅ Node 环境可用 `file://`（但当前项目不涉及）

### 5.4 默认模型下载源

如果不传 `textDetectionModelAsset` / `textRecognitionModelAsset`，但传了 `textDetectionModelName`，SDK 会按 `DEFAULT_MODEL_ASSETS` 表从 **百度 BCE Bos CDN** 下载 `.tar`。

⚠️ **这意味着仅指定 `lang + ocrVersion` 时，模型走 CDN**。要完全离线必须**同时**指定 `text*ModelAsset.url` 为本地路径。

---

## 6. 运行时配置（OrtOptions 与 wasm 资源）

来源 `packages/core/src/runtime/ort.ts` + 架构文档：

| 字段 | 说明 |
|------|------|
| `backend` | `'wasm'` / `'webgpu'` / `'auto'`。auto 优先 webgpu（如果 `navigator.gpu` 可用） |
| `wasmPaths` | ONNX Runtime Web 的 wasm 资源路径。**强烈建议显式设置**，尤其是 worker 模式 |
| `numThreads` | WASM 多线程数；非跨源隔离时必须为 1 |
| `simd` | 启用 SIMD 加速（现代浏览器基本都支持） |
| `proxy` / `disableWasmProxy` | 控制 ORT wasm proxy；**worker 模式 SDK 内部强制关闭 wasm proxy** |

`backend: 'webgpu'` 时会先 `navigator.gpu.requestAdapter()` 检查可用性；不可用则抛 `Error`。

**fallback 行为**（来自 architecture.md）：
- 主线程模式：不设 `wasmPaths` 时由 bundler 处理（Vite 会从 `node_modules/onnxruntime-web/dist/` 拷贝 `.wasm`）
- Worker 模式：不设 `wasmPaths` 时 fallback 到 jsdelivr CDN（**SDK 构建时锁定的 ORT 版本**），并在 console 警告

---

## 7. Worker 模式 vs 主线程模式

### 7.1 启动

```ts
const ocr = await PaddleOCR.create({
  lang: 'ch',
  ocrVersion: 'PP-OCRv5',
  worker: true,                          // ← 关键
  ortOptions: {
    backend: 'wasm',
    wasmPaths: 'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/',
    numThreads: 2,
    simd: true
  }
});
```

### 7.2 行为差异（来自 architecture.md）

- Worker 模式用包内 worker 路径（`packages/core/src/pipelines/ocr/worker-entry.ts`），**不是** ONNX Runtime Web 的 `env.wasm.proxy`
- 启用 `worker: true` 时 SDK 内部强制关闭 ORT wasm proxy（避免 worker 嵌套）
- 浏览器输入在**主线程**标准化为 transferable payload，再传入 worker
- `cv.Mat` **不能**作为 worker 输入（无法 transferable）；worker 模式用 `ImageBitmap` 传输
- Worker 模式下**不支持**自定义 `fetch`（`PaddleOCR.create` 会抛错）

### 7.3 自定义 Worker 工厂

```ts
const ocr = await PaddleOCR.create({
  worker: {
    createWorker: () => new MyCustomWorker()
  },
  // ...
});
```

---

## 8. 两种构造方式

### 8.1 直接参数（推荐，简单场景）

```ts
PaddleOCR.create({
  lang: 'ch',
  ocrVersion: 'PP-OCRv5',
  textDetectionModelName: 'PP-OCRv5_mobile_det',
  textRecognitionModelName: 'PP-OCRv5_mobile_rec',
  textDetectionModelAsset: { url: '/models/det.tar' },   // 可选：自定义资源地址
  textRecognitionModelAsset: { url: '/models/rec.tar' },
  textDetectionBatchSize: 2,
  textRecognitionBatchSize: 6,
  ortOptions: { backend: 'wasm', wasmPaths: '/ort-wasm/', numThreads: 2, simd: true }
});
```

支持的 `lang × ocrVersion` 组合（`SUPPORTED_LANG_VERSION_MODELS`）：

| lang | ocrVersion | 模型 |
|------|-----------|------|
| `ch`, `chinese_cht`, `en`, `japan` | `PP-OCRv5` | DEFAULT_MODEL_SELECTION |
| `ch`, `chinese_cht`, `en`, `japan`, 数十种拉丁语 | `PP-OCRv6` | `PP-OCRv6_small_*` |
| 任意 lang | 显式 `PP-OCRv6_tiny_*` | 按模型名解析 |

### 8.2 产线配置（YAML 风格，复杂场景）

```ts
PaddleOCR.create({
  pipelineConfig: `
    pipeline_name: OCR
    SubModules:
      TextDetection:
        model_name: PP-OCRv5_mobile_det
        batch_size: 2
      TextRecognition:
        model_name: PP-OCRv5_mobile_rec
        batch_size: 6
  `,
  ortOptions: { wasmPaths: '/ort-wasm/' }
});
```

支持的 pipeline YAML 字段：

```yaml
pipeline_name: OCR                # 必须为 "OCR"
batch_size: 1                     # pipeline 级 batch
text_type: general                # 默认 general（其他值会告警）
SubModules:
  TextDetection:
    model_name: PP-OCRv5_mobile_det
    batch_size: 2
    limit_side_len: 960
    limit_type: max                # 'min' | 'max'
    max_side_limit: 4000
    thresh: 0.3
    box_thresh: 0.6
    unclip_ratio: 2.0
    model_dir:                     # 自定义资源（可为 null 或 { url: '...' }）
      url: 'https://.../det.tar'
  TextRecognition:
    model_name: PP-OCRv5_mobile_rec
    batch_size: 6
    score_thresh: 0
```

`unsupportedBehavior: 'warn' | 'ignore' | 'error'` 控制 `DocPreprocessor` / `TextLineOrientation` 等暂不支持特性时的行为。

**优先级**：直接参数 > pipelineConfig > 默认值

---

## 9. 集成清单（Host Application 责任）

来自 architecture.md `Application responsibilities`：

### 9.1 HTTP 响应头（**必须**）

```ts
// vite.config.ts 已经设置：
server: {
  headers: {
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Embedder-Policy': 'credentialless'  // 或 'require-corp'
  }
}
```

**为什么要**：启用多线程 WASM / WebGPU 需要 SharedArrayBuffer，要求 cross-origin isolation。生产环境（nginx/CDN）也必须设置。

### 9.2 ONNX Runtime Web wasm 资源托管

至少选一种：

| 方案 | 说明 |
|------|------|
| **本地静态托管**（项目当前用法） | `wasmPaths: '/ort-wasm/'`，从 `frontend/public/ort-wasm/` 提供；`npm install onnxruntime-web` 后拷贝 `dist/*.wasm` |
| CDN | `wasmPaths: 'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/'`（注意锁定版本） |
| 由 bundler 处理 | 不设 `wasmPaths`（仅主线程模式）；Vite 会自动从 `node_modules/onnxruntime-web/dist/` 拷贝 |

### 9.3 模型资源托管

```ts
PaddleOCR.create({
  textDetectionModelAsset: { url: '/models/PP-OCRv5_mobile_det.tar' },
  textRecognitionModelAsset: { url: '/models/PP-OCRv5_mobile_rec.tar' }
});
```

放在 `frontend/public/models/*.tar`，遵守 §5.2 的归档约束。

### 9.4 构建工具

- 需要 bundler 支持 **module worker**（`type: 'module'` worker）；Vite 5+ / Webpack 5+ 默认支持
- 推荐 Vite manualChunks 把 SDK 拆出：`manualChunks: { paddleocr: ['@paddleocr/paddleocr-js'] }`（**项目当前已配置**：`frontend/vite.config.ts:35`）

---

## 10. 与 aigbooks 当前集成对照

| 项 | 当前实现 | 文档期望 | 是否符合 |
|----|---------|---------|---------|
| 包名 | `@paddleocr/paddleocr-js ^0.4.2` | 同 | ✅ |
| 构造 API | `PaddleOCR.create({...})` | 同 | ✅ |
| `lang` + `ocrVersion` | `ch` + `PP-OCRv5` | 受支持组合 | ✅ |
| `worker` | `false`（主线程） | 合法 | ✅ |
| `ortOptions.backend` | `wasm` | 合法 | ✅ |
| `ortOptions.wasmPaths` | `/ort-wasm/`（本地） | 合法且推荐 | ✅ |
| `ortOptions.simd` | `true` | 合法 | ✅ |
| `ortOptions.numThreads` | 根据 `crossOriginIsolated` 自适应 1~4 | 推荐做法 | ✅ |
| 模型资源 URL | 本地 `/models/PP-OCRv5_mobile_*.tar` | 合法（任意 fetch 可达 URL） | ✅ |
| `text*ModelName` | `PP-OCRv5_mobile_det` / `PP-OCRv5_mobile_rec` | DEFAULT_MODEL_ASSETS 中有 | ✅ |
| vite manualChunks | `paddleocr: ['@paddleocr/paddleocr-js']` | 推荐 | ✅ |
| COOP/COEP 响应头 | dev + preview 都设置了 | **必须** | ✅ |
| `fetch` 不被自定义 | ✅ | worker 模式下不允许；当前未用 worker，符合 | ✅ |
| `ocr.predict()` 返回类型解构 | `results[0]` | 与 demo 一致 | ✅ |

**结论：当前集成与官方推荐做法完全一致，无需改动**。本调研只为回答问题"是否支持本地模型路径"以及为后续可能的功能扩展（如切到 worker、可视化）提供文档基础。

---

## 11. Demo 应用集成参考（来自 `apps/demo/src/main.ts`）

关键实战片段：

```ts
import { PaddleOCR } from '@paddleocr/paddleocr-js';
import type { OcrResult, OcrResultItem } from '@paddleocr/paddleocr-js';
import { OcrVisualizer } from '@paddleocr/paddleocr-js/viz';

// 1) 准备线程数
function getDemoThreadCount(): number {
  return self.crossOriginIsolated
    ? Math.min(4, Math.max(1, (navigator.hardwareConcurrency || 2) - 1))
    : 1;
}

// 2) 懒加载 + 延迟初始化
state.ocr = await PaddleOCR.create({
  initialize: false,                         // 先不初始化
  worker: false,
  textDetectionModelName: `${preset}_det`,
  textRecognitionModelName: `${preset}_rec`,
  ortOptions: {
    backend: ui.runtimeBackend.value as 'auto' | 'webgpu' | 'wasm',
    wasmPaths: ORT_WASM_PATHS,
    numThreads: getDemoThreadCount(),
    simd: true
  }
});
const summary = await state.ocr.initialize();  // 手动初始化

// 3) 单图预测 + 提取首项
const [result] = await state.ocr.predict(state.imageFile, {
  textDetThresh: 0.3,
  textDetBoxThresh: 0.6,
  textDetUnclipRatio: 1.5,
  textRecScoreThresh: 0.1
});

// 4) 可视化
const visualizer = new OcrVisualizer({ font: { family: 'PingFang SC', source: '/fonts/xxx.ttf' } });
const blob = await visualizer.toBlob(bitmap, result);
```

**值得借鉴的模式**：
- `initialize: false` + 手动调 `initialize()`，便于显示初始化进度
- `getDemoThreadCount()` 模式：跨源隔离前=1，否则按 `hardwareConcurrency` 减 1 限到 4
- 可视化字体可远程加载（PingFang SC 远程 ttf）

---

## 12. 常见陷阱与排错

| 现象 | 可能原因 |
|------|----------|
| 初始化报 `Failed to download ... HTTP 404` | 模型 URL 路径写错，或 `.tar` 没放到 `public/` |
| 初始化报 `tar entries missing inference.onnx` | `.tar.gz` 或打包结构不对（SDK 不解压 gzip） |
| 初始化报 `model_name mismatch` | `inference.yml` 内的 `model_name` 与 `textDetectionModelName` / `textRecognitionModelName` 不一致 |
| `SharedArrayBuffer is not defined` | COOP/COEP 头未设置，或 HTTPS 配置问题 |
| Worker 模式报 `cv.Mat not supported` | 给 worker 传入了 `cv.Mat`；应改用 `ImageBitmap` |
| Worker 模式下 wasm 找不到 | 未设 `wasmPaths`，SDK fallback CDN 可能跨域/CSP 受阻；显式设 `wasmPaths` |
| `webgpu unavailable` | 浏览器不支持或无 GPU 适配器；改用 `backend: 'wasm'` |
| 模型下载慢 | CDN 受限/被墙；切到本地资源 |

---

## 13. 后续可选改进（不在本次范围）

| 方向 | 说明 |
|------|------|
| 切换到 `worker: true` | 不阻塞主线程；需补 `ortOptions.wasmPaths` |
| 切换到 `PP-OCRv6_small` 或 `_tiny` | 体积更小、速度更快；需要重新准备 `.tar` 资源 |
| 添加 `@paddleocr/paddleocr-js/viz` 可视化 | 调试用，prod 可能不需要 |
| 升级到 WebGPU | `backend: 'auto'`，浏览器自动选；用户态零改动 |
| 添加 `textRecScoreThresh` 等运行时调参 | 当作 user-tunable 参数暴露 |

---

## 附录 A：参考链接清单

- npm：https://www.npmjs.com/package/@paddleocr/paddleocr-js
- GitHub：https://github.com/PaddlePaddle/PaddleOCR/tree/main/paddleocr-js
- SDK 源码入口：https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr-js/packages/core/src/index.ts
- 关键实现：
  - 顶层入口：`packages/core/src/pipelines/ocr/index.ts`
  - 流水线运行器：`packages/core/src/pipelines/ocr/core.ts`
  - 选项归一化：`packages/core/src/pipelines/ocr/shared.ts`
  - 配置解析：`packages/core/src/pipelines/ocr/config.ts`
  - 运行时参数：`packages/core/src/pipelines/ocr/runtime-params.ts`
  - 模型资源：`packages/core/src/resources/model-asset.ts`
  - ORT 运行时：`packages/core/src/runtime/ort.ts`
  - 浏览器/Worker 适配：`packages/core/src/platform/browser.ts`
- Demo 应用：`packages/../apps/demo/`（含 `src/main.ts`、`vite.config.js`、`index.html`）
- 中文文档：`packages/core/README_cn.md`、`docs/architecture_cn.md`、`docs/development_cn.md`、`docs/monorepo_cn.md`、`README_cn.md`