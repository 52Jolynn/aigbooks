<template>
  <div class="camera-capture">
    <div v-if="!isSecureContext" class="camera-capture__error">
      <span class="camera-capture__error-icon" aria-hidden="true">!</span>
      <span>{{ report.cameraInsecureContext }}</span>
    </div>

    <template v-else>
      <div v-if="cameraError" class="camera-capture__error">
        <span class="camera-capture__error-icon" aria-hidden="true">!</span>
        <span>{{ cameraError }}</span>
        <button
          type="button"
          class="camera-capture__retry"
          @click="startCamera"
        >{{ report.retry }}</button>
      </div>

      <div v-else-if="!hasStream && !hasCapture" class="camera-capture__idle">
        <button
          type="button"
          class="camera-capture__btn camera-capture__btn--primary"
          :disabled="isStarting"
          :aria-busy="isStarting"
          @click="startCamera"
        >{{ isStarting ? report.cameraStarting : report.cameraStart }}</button>
      </div>

      <div v-else-if="hasStream" class="camera-capture__streaming">
        <video
          ref="videoRef"
          :class="['camera-capture__video', { 'camera-capture__video--facing-user': currentFacing === 'user' }]"
          autoplay
          playsinline
          muted
        />
        <div class="camera-capture__controls">
          <button
            type="button"
            class="camera-capture__btn camera-capture__btn--ghost"
            :aria-label="report.cameraSwitchFacing"
            @click="switchFacing"
          >{{ report.cameraSwitchFacing }}</button>
          <button
            type="button"
            class="camera-capture__btn camera-capture__btn--primary"
            :disabled="isCapturing"
            :aria-busy="isCapturing"
            @click="capture"
          >{{ report.cameraCapture }}</button>
          <button
            type="button"
            class="camera-capture__btn camera-capture__btn--ghost"
            @click="stopCamera"
          >{{ report.cameraCancel }}</button>
        </div>
      </div>

      <div v-else-if="hasCapture" class="camera-capture__captured">
        <img
          :src="capturedUrl!"
          :alt="report.cameraCapturedAlt"
          class="camera-capture__preview"
        />
        <div class="camera-capture__controls">
          <button
            type="button"
            class="camera-capture__btn camera-capture__btn--ghost"
            @click="retake"
          >{{ report.cameraRetake }}</button>
          <button
            type="button"
            class="camera-capture__btn camera-capture__btn--primary"
            @click="useCapture"
          >{{ report.cameraUse }}</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import { report } from '@/i18n/zh';

const props = withDefaults(
  defineProps<{
    facingMode?: 'user' | 'environment';
  }>(),
  { facingMode: 'environment' },
);
const emit = defineEmits<{ 'update:file': [File | null] }>();

const isSecureContext = computed(
  () => typeof window !== 'undefined' && window.isSecureContext,
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

watch(
  stream,
  (newStream) => {
    const v = videoRef.value;
    if (!v) return;
    if (newStream) {
      v.muted = true;
      v.srcObject = newStream;
      v.play().catch(() => {});
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

async function startCamera() {
  if (!isSecureContext.value) return;
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
    cameraError.value = report.cameraNotFound;
    return;
  }
  cameraError.value = null;
  isStarting.value = true;
  try {
    stopCamera();
    const s = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: currentFacing.value,
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });
    stream.value = s;
  } catch (err) {
    stream.value = null;
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
</script>

<style scoped>
.camera-capture {
  border: 1px dashed var(--surface-rule);
  border-radius: 12px;
  padding: 18px;
  background: var(--surface-tray);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.camera-capture__idle {
  display: flex;
  justify-content: center;
}

.camera-capture__video {
  width: 100%;
  aspect-ratio: 16 / 9;
  min-height: 240px;
  background: #000;
  border-radius: 8px;
  object-fit: contain;
  display: block;
}
.camera-capture__video--facing-user {
  transform: scaleX(-1);
}

.camera-capture__preview {
  width: 100%;
  max-height: 360px;
  object-fit: contain;
  background: var(--surface-deep);
  border-radius: 8px;
  display: block;
}

.camera-capture__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 10px;
}

.camera-capture__btn {
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
.camera-capture__btn:hover:not(:disabled) {
  border-color: var(--quarantine-ok);
  color: var(--quarantine-ok);
}
.camera-capture__btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.camera-capture__btn--primary {
  background: var(--quarantine-ok);
  color: #fff;
  border-color: var(--quarantine-ok);
}
.camera-capture__btn--primary:hover:not(:disabled) {
  background: var(--ink-deep);
  border-color: var(--ink-deep);
  color: #fff;
}
</style>
