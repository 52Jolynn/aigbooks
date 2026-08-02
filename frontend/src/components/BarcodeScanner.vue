<template>
  <div class="barcode-scanner">
    <div v-if="!isSecureContext" class="barcode-scanner__error">
      <span class="barcode-scanner__error-icon" aria-hidden="true">!</span>
      <span>{{ report.cameraInsecureContext }}</span>
    </div>

    <template v-else>
      <div v-if="error" class="barcode-scanner__error">
        <span class="barcode-scanner__error-icon" aria-hidden="true">!</span>
        <span>{{ error }}</span>
        <button
          type="button"
          class="barcode-scanner__retry"
          @click="startScan"
        >{{ report.retry }}</button>
      </div>

      <div v-else-if="!hasStream && !scannedResult" class="barcode-scanner__idle">
        <button
          type="button"
          class="barcode-scanner__btn barcode-scanner__btn--primary"
          :disabled="isStarting"
          :aria-busy="isStarting"
          @click="startScan"
        >{{ isStarting ? report.barcodeScannerStarting : report.barcodeScannerStart }}</button>
      </div>

      <div v-else-if="hasStream" class="barcode-scanner__streaming">
        <div
          class="barcode-scanner__video-wrap"
          @click="onVideoClick"
        >
          <video
            ref="videoRef"
            class="barcode-scanner__video"
            autoplay
            playsinline
            muted
          />
          <div class="barcode-scanner__overlay" aria-hidden="true">
            <div class="barcode-scanner__reticle" />
          </div>
        </div>
        <p class="barcode-scanner__hint">{{ report.barcodeScannerHint }}</p>
        <div class="barcode-scanner__controls">
          <button
            type="button"
            class="barcode-scanner__btn barcode-scanner__btn--ghost"
            @click="stopScan"
          >{{ report.cameraCancel }}</button>
        </div>
      </div>

      <div v-else-if="scannedResult" class="barcode-scanner__captured">
        <p class="barcode-scanner__result">
          <span class="barcode-scanner__result-label">{{ report.barcodeScannerScanned }}：</span>
          <strong>{{ scannedResult.isbn || scannedResult.issn }}</strong>
        </p>
        <div class="barcode-scanner__controls">
          <button
            type="button"
            class="barcode-scanner__btn barcode-scanner__btn--ghost"
            @click="retake"
          >{{ report.barcodeRetake }}</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import { recognizeBarcodes, type BarcodeResult } from '@/barcode';
import { report } from '@/i18n/zh';

const emit = defineEmits<{
  'update:identifier': [{ isbn?: string; issn?: string; type: 'isbn' | 'issn' }];
}>();

const isSecureContext = computed(
  () => typeof window !== 'undefined' && window.isSecureContext,
);

const stream = ref<MediaStream | null>(null);
const videoRef = ref<HTMLVideoElement | null>(null);
const isStarting = ref(false);
const error = ref<string | null>(null);
const scannedResult = ref<BarcodeResult | null>(null);

const hasStream = computed(() => stream.value !== null);

let scanInterval: ReturnType<typeof setInterval> | null = null;

watch(
  stream,
  (newStream) => {
    const v = videoRef.value;
    if (!v) return;
    if (newStream) {
      v.muted = true;
      v.srcObject = newStream;
      console.log('[barcode-scanner] watch(stream) 绑定 srcObject');
      v.play()
        .then(() => console.log('[barcode-scanner] watch(stream) v.play() 成功，videoWidth:', v.videoWidth))
        .catch((e) => console.warn('[barcode-scanner] watch(stream) v.play() 失败：', e));
    } else {
      v.srcObject = null;
    }
  },
  { flush: 'post' },
);

function mapMediaError(err: unknown): string {
  const name = err instanceof Error ? err.name : '';
  if (name === 'NotAllowedError' || name === 'SecurityError') {
    return report.cameraNotAllowed;
  }
  if (name === 'NotFoundError' || name === 'OverconstrainedError') {
    return report.cameraNotFound;
  }
  if (name === 'NotReadableError' || name === 'TrackStartError') {
    return report.cameraInUse;
  }
  return report.cameraGeneric;
}

const debugMode =
  typeof window !== 'undefined' &&
  new URLSearchParams(window.location.search).has('ocr-debug');

function logDebug(...args: unknown[]) {
  if (debugMode) console.log('[barcode-scanner]', ...args);
}

async function onVideoClick() {
  const v = videoRef.value;
  if (!v) return;
  try {
    await v.play();
    logDebug('user-click play() 成功');
  } catch (e) {
    console.warn('[barcode-scanner] user-click play() 失败：', e);
  }
}

async function startScan() {
  console.log('[barcode-scanner] startScan 被调用');
  if (!isSecureContext.value) {
    console.warn('[barcode-scanner] 非 secure context（需 HTTPS 或 localhost），isSecureContext =', isSecureContext.value);
    return;
  }
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
    console.warn('[barcode-scanner] 浏览器不支持 mediaDevices / getUserMedia');
    error.value = report.cameraNotFound;
    return;
  }
  console.log('[barcode-scanner] secure context OK，has getUserMedia =', typeof navigator.mediaDevices.getUserMedia);
  error.value = null;
  scannedResult.value = null;
  isStarting.value = true;
  try {
    stopScan();
    console.log('[barcode-scanner] 调用 getUserMedia({ video: { facingMode: "environment" }})');
    const s = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment',
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
    console.log('[barcode-scanner] getUserMedia 成功，tracks:', s.getTracks().map((t) => ({
      kind: t.kind,
      readyState: t.readyState,
      enabled: t.enabled,
      muted: t.muted,
      label: t.label,
    })));
    stream.value = s;
    if (debugMode) {
      const devices = await navigator.mediaDevices.enumerateDevices();
      console.log('[barcode-scanner] enumerateDevices:', devices.map((d) => ({
        kind: d.kind,
        label: d.label,
        deviceId: d.deviceId.slice(0, 8),
      })));
    }
    // srcObject 绑定由 watch(stream, { flush: 'post' }) 处理
    scanInterval = setInterval(scanOnce, 500);
    console.log('[barcode-scanner] 扫描循环已启动');
  } catch (err) {
    console.error('[barcode-scanner] getUserMedia 失败：', err);
    stream.value = null;
    error.value = mapMediaError(err);
  } finally {
    isStarting.value = false;
  }
}

function stopScan() {
  if (scanInterval !== null) {
    clearInterval(scanInterval);
    scanInterval = null;
  }
  if (stream.value) {
    stream.value.getTracks().forEach((t) => t.stop());
    stream.value = null;
  }
  if (videoRef.value) {
    videoRef.value.srcObject = null;
  }
}

let scanCount = 0;

async function scanOnce() {
  const video = videoRef.value;
  scanCount++;
  console.log(`[barcode-scanner] scanOnce #${scanCount} called, video=${!!video}, stream=${!!stream.value}`);
  if (!video || !stream.value) {
    return;
  }
  if (video.readyState < 2) {
    console.log(`[barcode-scanner] scanOnce #${scanCount} skip: readyState=${video.readyState}`);
    return;
  }
  try {
    const result = await recognizeBarcodes(video);
    console.log(`[barcode-scanner] scanOnce #${scanCount} 结果：`, result);
    if (result.isbn || result.issn) {
      console.log('[barcode-scanner] 识别成功：', result);
      scannedResult.value = result;
      stopScan();
      emit('update:identifier', {
        isbn: result.isbn,
        issn: result.issn,
        type: result.isbn ? 'isbn' : 'issn',
      });
    }
  } catch (e) {
    console.warn('[barcode-scanner] scan 失败：', e);
  }
}

function retake() {
  scannedResult.value = null;
  void startScan();
}

onUnmounted(() => {
  stopScan();
});
</script>

<style scoped>
.barcode-scanner {
  border: 1px dashed var(--surface-rule);
  border-radius: 12px;
  padding: 18px;
  background: var(--surface-tray);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.barcode-scanner__idle {
  display: flex;
  justify-content: center;
}

.barcode-scanner__video-wrap {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.barcode-scanner__video {
  width: 100%;
  aspect-ratio: 16 / 9;
  min-height: 240px;
  background: #000;
  border-radius: 8px;
  object-fit: cover;
  display: block;
}

.barcode-scanner__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.barcode-scanner__reticle {
  width: 75%;
  max-width: 360px;
  aspect-ratio: 3 / 1;
  border: 2px solid var(--quarantine-ok);
  border-radius: 8px;
  box-shadow:
    0 0 0 1px rgba(14, 107, 82, 0.3),
    0 0 0 9999px transparent;
  background: transparent;
}

.barcode-scanner__hint {
  text-align: center;
  font-family: var(--font-cn);
  font-size: 13px;
  color: var(--ink-soft);
  margin: 0;
}

.barcode-scanner__result {
  text-align: center;
  font-family: var(--font-cn);
  font-size: 14px;
  color: var(--ink);
  margin: 0;
}
.barcode-scanner__result strong {
  font-family: var(--font-mono);
  color: var(--quarantine-ok);
  font-weight: 500;
  margin-left: 6px;
}

.barcode-scanner__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 4px;
}

.barcode-scanner__btn {
  font-family: var(--font-cn);
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid var(--surface-rule);
  background: #fff;
  color: var(--ink);
  transition: border-color var(--transition-fast), color var(--transition-fast), background var(--transition-fast);
}
.barcode-scanner__btn:hover:not(:disabled) {
  border-color: var(--quarantine-ok);
  color: var(--quarantine-ok);
}
.barcode-scanner__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.barcode-scanner__btn--primary {
  background: var(--quarantine-ok);
  color: #fff;
  border-color: var(--quarantine-ok);
}
.barcode-scanner__btn--primary:hover:not(:disabled) {
  background: var(--ink-deep);
  border-color: var(--ink-deep);
  color: #fff;
}
</style>
