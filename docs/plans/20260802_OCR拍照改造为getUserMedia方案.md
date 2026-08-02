---
创建时间: 2026-08-02 19:30
状态: 已完成
---

# OCR 拍照改造为 getUserMedia 方案

> 范围：仅修改 `frontend/`（新增 `CameraCapture.vue`、重构 `ReportView.vue`、补 i18n 文案），不引入新依赖，不修改 `node_modules/`、`backend/`。
> 决策背景：桌面 Chrome / Firefox / Safari **按 HTML 规范忽略 `<input capture="environment">`**，一律走文件选择器。要让桌面端也能拍照，必须改用 `getUserMedia` + `<video>` + Canvas 抓帧方案（参考 `mario-tools/src/components/tools/camera-capture/index.tsx`）。
> 沿用：上次的"OCR 支持拍照/上传"功能（mode 切换、清空 ocrFiles、HEIC 转码、移动端 input capture 修复）保留——但拍照模式从 input 方案改为 CameraCapture 组件。

---

## 0. 计划概述

- **目标**：OCR 区块拍照模式改用 `getUserMedia` 实时预览 + Canvas 抓帧方案，让桌面端 + 移动端都能真正拍照
- **范围**：
  - 新增 `CameraCapture.vue` 组件（~200 行）
  - 重构 `ReportView.vue` OCR 区块（mode 切换逻辑保留，拍照模式改渲染 CameraCapture）
  - i18n 新增 ~10 条 key
- **不在范围**：
  - 移动端 `<input capture>` 修复保留不删（其他场景可能用到）—— 仍支持，但本次 OCR 拍照走新方案
  - 视频录制 / 前后置切换动画 / 多帧连拍
  - 图片预处理（缩放到 1280px）—— 留作下一轮
- **预期成果**：
  - 移动端：点"拍照" → "启动摄像头" → `<video>` 实时预览 → 点"拍摄" → 显示抓帧图 → 点"使用此照片"自动喂 OCR
  - 桌面端：点"拍照" → "启动摄像头" → 弹权限申请 + `<video>` 实时预览 → 同上
  - 关闭 / 切换 mode 时 stream 严格清理（`getTracks().forEach(t => t.stop())`）
  - secure context 检测、错误分类（NotAllowedError / NotFoundError / NotReadableError）
  - `pnpm typecheck` / `pnpm build` 通过
- **预计工时**：0.8 个工作日

---

## 1. 需求背景

- **原始需求**：OCR 扫描要支持拍照、上传图片两种模式
- **澄清记录**（沿用上次 + 本次补充）：
  - 上次：mode 切换 tab、一次一张图、文案朴实直白、桌面端降级
  - 本次：桌面端降级方案由"input capture 走文件选择器"改为"getUserMedia 走实时预览"
- **业务价值**：
  - 桌面端用户也能拍照（之前只能选文件，体验差）
  - 移动端实时预览所见即所得（之前需要先打开相机 app 拍好再回来选）
- **成功标准**：
  1. 桌面 Chrome / 移动 Safari / 移动 Chrome：点"启动摄像头" → 弹权限申请 → 实时预览 → 拍摄 → 喂 OCR
  2. 非 secure context（HTTP 非 localhost）→ 显示明确提示
  3. 摄像头权限被拒 → 显示明确错误 + "重试"按钮
  4. 无可用摄像头（PC 无摄像头）→ 显示明确错误
  5. 切到"上传图片"或关闭表单 → stream 立即停止（不持续占用摄像头）
  6. iOS Safari 不全屏接管（`playsInline` 关键）
  7. `pnpm typecheck` + `pnpm build` 通过

---

## 2. 影响范围

### 2.1 预计影响文件

| # | 文件路径 | 变更等级 | 变更性质 |
|---|---|---|---|
| 1 | `frontend/src/components/CameraCapture.vue` | NEW | 实时预览 + 抓帧组件，~200 行 |
| 2 | `frontend/src/views/ReportView.vue` | MEDIUM | OCR 区块拍照模式改渲染 CameraCapture |
| 3 | `frontend/src/i18n/zh.ts` | LOW | 新增 ~10 条 key |
| 4 | `frontend/src/styles/dossier.css` | LOW | 新增 `.camera-capture__*` 全局样式 |

### 2.2 不涉及
- 数据库变更：否
- 新增依赖：否（`getUserMedia` / `<video>` / Canvas 都是浏览器原生 API）
- 后端 API 变更：否
- `FileUploader` 的 `capture` prop 保留不删（向后兼容）
- `ocr/index.ts` 沿用上次单例 worker 修复

---

## 3. 设计原则遵循

- **mario-tools 模式对齐**：
  - `getUserMedia({ video: { facingMode, width, height }, audio: false })`
  - `<video ref={videoRef} autoPlay playsInline muted>` 三件套缺一不可
  - Canvas 抓帧：`canvas.width = videoWidth; canvas.height = videoHeight; ctx.drawImage(video)`
  - 严格 stream 清理：`getTracks().forEach(t => t.stop())` + `video.srcObject = null`
- **状态机明确**：idle → starting → streaming → captured → (use | retake) → streaming/idle
- **错误分类**：NotAllowedError / NotFoundError / NotReadableError / OverconstrainedError + 通用 fallback
- **secure context 守卫**：非 secure context（HTTP 非 localhost）提前显示错误，不让用户走到 getUserMedia 才失败
- **a11y**：按钮文字明确、`aria-label`、`aria-busy` 标识 loading
- **i18n 单源**：所有新增文案进 `report` 命名空间

---

## 4. 任务分解与代码清单

### 任务 1：新增 `CameraCapture.vue` 组件 [P0, 1.5h]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 新增 | `frontend/src/components/CameraCapture.vue` | 实时预览 + 抓帧组件 |

#### 代码调整清单

| 操作 | 代码块/模块 | 说明 |
|------|------------|------|
| 新增 | Props | `maxSize?: number`（默认 20MB）、`facingMode?: 'user' \| 'environment'`（默认 environment） |
| 新增 | Emits | `update:file: [File \| null]`——用户点击"使用此照片"时 emit；切回"重拍"时 emit null |
| 新增 | Refs | `stream`、`videoRef`、`isStarting`、`isCapturing`、`cameraError`、`capturedBlob`、`capturedUrl` |
| 新增 | Computed | `isSecureContext`、`hasStream`、`hasCapture` |
| 新增 | `startCamera()` | 调 `getUserMedia`，绑定 stream 到 video，捕获错误映射到 i18n 文案 |
| 新增 | `stopCamera()` | `stream.getTracks().forEach(t => t.stop())` + `streamRef = null` + `video.srcObject = null` |
| 新增 | `capture()` | Canvas 抓帧 → `canvas.toBlob('image/jpeg', 0.92)` → 存 capturedBlob/Url → 自动 stopCamera |
| 新增 | `useCapture()` | emit `update:file: new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' })` |
| 新增 | `retake()` | 释放 capturedUrl → 重新 startCamera |
| 新增 | `mapMediaError(err)` | NotAllowedError / NotFoundError / NotReadableError / OverconstrainedError 映射到 i18n key |
| 新增 | `onUnmounted` | 自动 stopCamera（防 stream 泄漏） |

#### 测试用例调整清单

无（项目暂无测试框架）

#### 核心设计要点

```vue
<template>
  <div class="camera-capture">
    <div v-if="!isSecureContext" class="camera-capture__error">
      <span>{{ report.cameraInsecureContext }}</span>
    </div>

    <template v-else>
      <div v-if="cameraError" class="camera-capture__error">
        <span>{{ cameraError }}</span>
        <button type="button" @click="startCamera">{{ report.retry }}</button>
      </div>

      <div v-else-if="!hasStream && !hasCapture" class="camera-capture__idle">
        <button
          type="button"
          class="camera-capture__start"
          :disabled="isStarting"
          :aria-busy="isStarting"
          @click="startCamera"
        >
          {{ isStarting ? report.cameraStarting : report.cameraStart }}
        </button>
      </div>

      <div v-else-if="hasStream" class="camera-capture__streaming">
        <video
          ref="videoRef"
          class="camera-capture__video"
          autoplay
          playsinline
          muted
        />
        <div class="camera-capture__controls">
          <button
            type="button"
            class="camera-capture__switch"
            :aria-label="report.cameraSwitchFacing"
            @click="switchFacing"
          >{{ report.cameraSwitchFacing }}</button>
          <button
            type="button"
            class="camera-capture__capture-btn"
            @click="capture"
          >{{ report.cameraCapture }}</button>
          <button
            type="button"
            class="camera-capture__cancel"
            @click="stopCamera"
          >{{ report.cameraCancel }}</button>
        </div>
      </div>

      <div v-else-if="hasCapture" class="camera-capture__captured">
        <img :src="capturedUrl!" :alt="report.cameraCapturedAlt" class="camera-capture__preview" />
        <div class="camera-capture__controls">
          <button type="button" class="camera-capture__retake" @click="retake">
            {{ report.cameraRetake }}
          </button>
          <button type="button" class="camera-capture__use" @click="useCapture">
            {{ report.cameraUse }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
```

```ts
// script setup 核心
import { computed, onUnmounted, ref } from 'vue';
import { report } from '@/i18n/zh';

const props = withDefaults(
  defineProps<{
    maxSize?: number;
    facingMode?: 'user' | 'environment';
  }>(),
  { maxSize: 20 * 1024 * 1024, facingMode: 'environment' },
);
const emit = defineEmits<{ 'update:file': [File | null] }>();

const isSecureContext = computed(() =>
  typeof window !== 'undefined' && window.isSecureContext,
);

const stream = ref<MediaStream | null>(null);
const videoRef = ref<HTMLVideoElement | null>(null);
const isStarting = ref(false);
const isCapturing = ref(false);
const cameraError = ref<string | null>(null);
const capturedBlob = ref<Blob | null>(null);
const capturedUrl = ref<string | null>(null);
const currentFacing = ref(props.facingMode);

const hasStream = computed(() => stream.value !== null);
const hasCapture = computed(() => capturedBlob.value !== null);

async function startCamera() {
  if (!isSecureContext.value) return;
  cameraError.value = null;
  isStarting.value = true;
  try {
    stopCamera();
    const s = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: currentFacing.value, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    stream.value = s;
    if (videoRef.value) {
      videoRef.value.srcObject = s;
      await videoRef.value.play().catch(() => {});
    }
  } catch (err) {
    cameraError.value = mapMediaError(err);
  } finally {
    isStarting.value = false;
  }
}

function stopCamera() {
  if (stream.value) {
    stream.value.getTracks().forEach((t) => t.stop());
    stream.value = null;
  }
  if (videoRef.value) {
    videoRef.value.srcObject = null;
  }
}

function mapMediaError(err: unknown): string {
  const name = err instanceof Error ? err.name : '';
  if (name === 'NotAllowedError') return report.cameraNotAllowed;
  if (name === 'NotFoundError') return report.cameraNotFound;
  if (name === 'NotReadableError') return report.cameraInUse;
  if (name === 'OverconstrainedError') return report.cameraNotFound;
  return report.cameraGeneric;
}

async function capture() {
  const video = videoRef.value;
  if (!video || !stream.value) return;
  isCapturing.value = true;
  try {
    const w = video.videoWidth;
    const h = video.videoHeight;
    if (w === 0 || h === 0) {
      cameraError.value = report.cameraNotReady;
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      cameraError.value = report.cameraGeneric;
      return;
    }
    if (currentFacing.value === 'user') {
      ctx.translate(w, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, w, h);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.92),
    );
    if (!blob) {
      cameraError.value = report.cameraGeneric;
      return;
    }
    if (capturedUrl.value) URL.revokeObjectURL(capturedUrl.value);
    capturedBlob.value = blob;
    capturedUrl.value = URL.createObjectURL(blob);
    stopCamera();
  } finally {
    isCapturing.value = false;
  }
}

function useCapture() {
  if (!capturedBlob.value) return;
  const file = new File(
    [capturedBlob.value],
    `camera-capture-${Date.now()}.jpg`,
    { type: 'image/jpeg' },
  );
  emit('update:file', file);
}

function retake() {
  if (capturedUrl.value) {
    URL.revokeObjectURL(capturedUrl.value);
    capturedUrl.value = null;
  }
  capturedBlob.value = null;
  emit('update:file', null);
  void startCamera();
}

async function switchFacing() {
  currentFacing.value = currentFacing.value === 'environment' ? 'user' : 'environment';
  await startCamera();
}

onUnmounted(() => {
  stopCamera();
  if (capturedUrl.value) URL.revokeObjectURL(capturedUrl.value);
});
```

#### scoped 样式
- `.camera-capture__video`：16:9 容器 + `object-fit: cover`
- `.camera-capture__preview`：保持原始比例，`max-height: 360px`
- `.camera-capture__start` / `__capture-btn` / `__use`：主操作（`--quarantine-ok` 实底 + 中文 display 字体）
- `.camera-capture__retake` / `__switch` / `__cancel`：次要操作（白底 + 描边）
- `.camera-capture__error`：警告橙（`--quarantine-warn-soft` 底）

#### 全局 dossier.css 新增
仅给需要"整行"效果的元素加全局类（避免 scoped 局限）：
- `.camera-capture__error`：整行错误提示，与 `.form-error` 同风格

---

### 任务 2：重构 `ReportView.vue` OCR 区块 [P0, 0.5h]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 修改 | `frontend/src/views/ReportView.vue` | OCR 区块拍照模式改渲染 CameraCapture |

#### 代码调整清单

| 操作 | 代码块/模块 | 说明 |
|------|------------|------|
| 新增 | `import CameraCapture from '@/components/CameraCapture.vue'` | 引入新组件 |
| 新增 | `function onCameraFile(file: File \| null)` | CameraCapture 的 emit 处理器，把 file 写进 ocrFiles（File[]），file 为 null 时清空 |
| 修改 | 模板 OCR section (L9-49) | ① mode 切换 radiogroup 不变；② `ocrMode === 'upload'` 渲染 FileUploader；③ `ocrMode === 'camera'` 渲染 CameraCapture |
| 删除 | `:capture` prop 传递 | 拍照模式不再走 input capture |

#### 核心设计要点

```vue
<!-- OCR section 改造后 -->
<div class="report-form__ocr-mode" role="radiogroup" :aria-label="report.ocrModeLabel">
  <button
    v-for="m in (['upload', 'camera'] as const)"
    :key="m"
    type="button"
    role="radio"
    :aria-checked="ocrMode === m"
    class="type-chip"
    :class="{ 'is-active': ocrMode === m }"
    @click="setOcrMode(m)"
  >{{ m === 'upload' ? report.ocrModeUpload : report.ocrModeCamera }}</button>
</div>

<component
  :is="ocrMode === 'camera' ? CameraCapture : FileUploader"
  v-bind="ocrMode === 'camera' ? {} : {
    accept: 'image/*',
    label: report.ocrModeUpload,
  }"
  :files="ocrFiles"
  @update:files="onOCRFiles"
  @update:file="onCameraFile"
/>
```

> **不**用 `<component :is>` 动态切换——因为 CameraCapture 和 FileUploader 的 props/emit 不同，容易出 TS 错误。改用 `v-if` 显式分支：

```vue
<FileUploader
  v-if="ocrMode === 'upload'"
  :files="ocrFiles"
  accept="image/*"
  :label="report.ocrModeUpload"
  @update:files="onOCRFiles"
/>
<CameraCapture
  v-else
  @update:file="onCameraFile"
/>
```

#### OCR 按钮逻辑调整

不需修改：
- "运行识别"按钮仍然在有 `ocrFiles[0]` 时可点
- `runOCR()` 不变（仍调 `recognizeText(ocrFiles.value[0])`）
- `onOCRFiles(files)` 和 `onCameraFile(file)` 都把数据写进 `ocrFiles`（一个用 array，一个用单 file 包成 array）

```ts
function onCameraFile(file: File | null) {
  ocrFiles.value = file ? [file] : [];
}
```

---

### 任务 3：i18n 文案补充 [P0, 0.2h]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 修改 | `frontend/src/i18n/zh.ts` | `report` 命名空间新增 ~10 条 key |

#### 代码调整清单

| 操作 | 代码块/模块 | 说明 |
|------|------------|------|
| 新增 | `report.cameraStart: '启动摄像头'` | 启动按钮文案 |
| 新增 | `report.cameraStarting: '启动中…'` | 启动 loading |
| 新增 | `report.cameraCapture: '拍摄'` | 拍摄按钮 |
| 新增 | `report.cameraRetake: '重拍'` | 拍摄后重拍 |
| 新增 | `report.cameraUse: '使用此照片'` | 拍摄后确认使用 |
| 新增 | `report.cameraSwitchFacing: '切换前后置'` | 前后置切换 |
| 新增 | `report.cameraCancel: '取消'` | 取消预览 |
| 新增 | `report.cameraInsecureContext: '请使用 HTTPS 或 localhost 访问以使用摄像头'` | 非 secure context |
| 新增 | `report.cameraNotAllowed: '摄像头权限被拒绝，请检查浏览器设置'` | NotAllowedError |
| 新增 | `report.cameraNotFound: '未检测到可用摄像头'` | NotFoundError / OverconstrainedError |
| 新增 | `report.cameraInUse: '摄像头正被其他程序占用'` | NotReadableError |
| 新增 | `report.cameraNotReady: '视频流尚未就绪，请稍候再试'` | videoWidth=0 |
| 新增 | `report.cameraGeneric: '摄像头启动失败'` | 通用错误 |
| 新增 | `report.cameraCapturedAlt: '已拍摄的照片预览'` | img alt |
| 新增 | `report.retry: '重试'` | 错误重试按钮（也可放 `consoleMessages`，但 `report` 更一致） |
| 删除 | `report.captureUnavailable` | 桌面端降级提示不再需要（getUserMedia 方案桌面端也能用） |
| 保留 | `report.ocrEmptyHint` | 占位提示，未来可能用 |

---

### 任务 4：全局样式 [P0, 0.2h]

#### 文件调整清单

| 操作 | 文件路径 | 说明 |
|------|---------|------|
| 修改 | `frontend/src/styles/dossier.css` | 新增 `.camera-capture__*` 整行效果样式 |

#### 代码调整清单

| 操作 | 代码块/模块 | 说明 |
|------|------------|------|
| 新增 | `.camera-capture` | 整块容器，与 `.file-uploader` 同风格（虚线边框 + 圆角 + 冷白底） |
| 新增 | `.camera-capture__error` | 整行错误提示（橙底 + 警告图标 + 重试按钮） |
| 新增 | `.camera-capture__start` | 主操作按钮（`--quarantine-ok` 实底） |
| 新增 | `.camera-capture__video` | 16:9 video 容器 |
| 新增 | `.camera-capture__preview` | 拍后预览图 |
| 新增 | `.camera-capture__controls` | 按钮组（flex + gap） |
| 新增 | `.camera-capture__capture-btn` / `__use` | 主操作 |
| 新增 | `.camera-capture__retake` / `__switch` / `__cancel` | 次要操作 |

---

## 5. 测试计划

| 测试类型 | 覆盖范围 | 验收标准 |
|---------|---------|---------|
| **类型检查** | `pnpm typecheck` | 0 error |
| **构建验证** | `pnpm build` | success |
| **手动 E2E（桌面 Chrome）** | 启动摄像头 | 弹权限申请 → 实时预览 → 拍摄 → 喂 OCR |
| **手动 E2E（移动 Safari/Chrome）** | 启动摄像头 | 同上，无全屏接管（playsInline） |
| **手动 E2E（拒绝权限）** | NotAllowedError | 显示明确错误 + 重试按钮 |
| **手动 E2E（无摄像头）** | 桌面无摄像头 | 显示"未检测到可用摄像头" |
| **手动 E2E（HTTP 非 secure）** | secure context 守卫 | 立即显示 HTTPS 提示，不调 getUserMedia |
| **手动 E2E（stream 清理）** | 切 mode / 关闭页面 | stream.getTracks() 全部 stopped，摄像头指示灯熄灭 |
| **手动 E2E（OCR 联动）** | 拍摄后"使用此照片" | 自动填入 ocrFiles，点"运行识别"调用 recognizeText |

---

## 6. 风险与应对

| # | 风险 | 概率 | 影响 | 应对措施 |
|---|------|------|------|---------|
| R1 | iOS Safari 不支持 `enumerateDevices` 时 `getUserMedia` 失败 | 中 | 中 | 仅用 `facingMode: 'environment'`，不预先 `enumerateDevices` |
| R2 | Android Chrome 某些版本 `videoWidth` 异步就绪 | 中 | 中 | `capture()` 内已检查 `w === 0 \|\| h === 0` 并返回 cameraNotReady 错误 |
| R3 | 桌面无摄像头 | 高（PC） | 低 | 显示明确 cameraNotFound 错误，用户可切"上传图片"模式 |
| R4 | stream 泄漏（组件卸载未停止） | 中 | 中 | `onUnmounted` 自动 stopCamera + revokeObjectURL |
| R5 | iOS Safari 全屏接管 video | 高 | 中 | `playsInline` 属性 + `muted` 强制属性（iOS 自动播放前置） |
| R6 | secure context 检测误判（某些内网） | 中 | 低 | 仅检测 `window.isSecureContext`，HTTP localhost 也算 secure |
| R7 | 拍摄后 JPEG 太大（>20MB） | 低 | 中 | `toBlob('image/jpeg', 0.92)` 已压缩；20MB 限制由 ocr 入口 maxSize 保证 |
| R8 | `videoRef.value.play()` reject（autoplay 策略） | 低 | 低 | `.catch(() => {})` 静默吞掉，stream 仍然有效 |

---

## 7. 实施顺序

1. 任务 3（i18n 文案）→ 先把 key 加好
2. 任务 1（CameraCapture.vue）→ 主战场
3. 任务 4（dossier.css）→ 配合任务 1
4. 任务 2（ReportView 重构）→ 串联起来
5. 任务 5（验证）→ typecheck + build

---

## 8. 验证清单（任务完成前逐项打勾）

- [ ] `pnpm typecheck` 通过
- [ ] `pnpm build` 通过
- [ ] 桌面 Chrome + 摄像头：点"启动摄像头" → 弹权限 → 预览 → 拍摄 → 喂 OCR
- [ ] 移动 Safari（iOS）：`playsInline` 生效，不全屏接管
- [ ] 移动 Chrome（Android）：同桌面
- [ ] 拒绝摄像头权限：显示明确错误 + 重试按钮
- [ ] 桌面无摄像头：显示"未检测到可用摄像头"
- [ ] HTTP 非 secure context：立即显示 HTTPS 提示
- [ ] 切到"上传图片"：stream 立即停止（Mac 摄像头指示灯熄灭 / Windows 摄像头图标消失）
- [ ] 关闭 `/reports/new` 页面：stream 立即停止
- [ ] 上传图片模式：行为与改造前完全一致
- [ ] 现有 6 处 FileUploader 调用方未受影响（capture prop 仍保留）

---

## 9. 后续迭代候选（不属本期）

- 图片预处理：拍摄后缩放到短边 ≤ 1280px（解决高分辨率原图）
- 拍摄历史：保留最近 N 张
- 闪光灯 / 网格 / 缩放控件
- 视频模式（短录）
- 把 `getUserMedia` 抽成 `useCamera()` 公共 composable
- 把 `.chip` 提取到 dossier.css 全局（消除 `.type-chip` 重复）

---

## 10. 与上次计划的关系

- 上次「OCR 支持拍照/上传」已实施：
  - 模式切换 tab ✓
  - 桌面端 input capture 降级（这次废弃）✓
  - HEIC 转码 ✓
  - tesseract.js 单例 worker + 超时 ✓
- 本次：
  - 拍照从 `<input capture>` 改为 `getUserMedia` + 实时预览
  - 保留上次其他所有功能
