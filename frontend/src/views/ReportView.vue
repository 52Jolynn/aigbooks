<template>
  <main class="ledger">
    <SectionHeader
      :num="report.sectionNum"
      :title="report.sectionTitle"
      :meta="report.sectionMeta"
    />
    <form class="report-form" novalidate @submit.prevent="onSubmit">
      <section class="report-form__section">
        <header class="report-form__heading">
          <h3 class="report-form__title">1 · {{ report.sectionOcr }}</h3>
          <span class="report-form__hint">{{ report.sectionOcrHint }}</span>
        </header>
        <div
          class="report-form__ocr-mode"
          role="radiogroup"
          :aria-label="report.ocrModeLabel"
        >
          <button
            v-for="m in (['upload', 'barcode', 'camera'] as const)"
            :key="m"
            type="button"
            role="radio"
            :aria-checked="ocrMode === m"
            class="type-chip"
            :class="{ 'is-active': ocrMode === m }"
            @click="setOcrMode(m)"
          >{{ modeLabel(m) }}</button>
        </div>
        <p class="report-form__ocr-tip">{{ modeTip(ocrMode) }}</p>
        <FileUploader
          v-if="ocrMode === 'upload'"
          :files="ocrFiles"
          accept="image/*"
          :label="modeLabel(ocrMode)"
          @update:files="onOCRFiles"
        />
        <BarcodeScanner
          v-else-if="ocrMode === 'barcode'"
          @update:identifier="onBarcodeIdentified"
        />
        <CameraCapture
          v-else
          @update:file="onCameraFile"
        />
        <div
          v-if="ocrMode !== 'barcode' && (ocrFiles[0] || ocrLoading)"
          class="recognition-steps"
          role="status"
          aria-live="polite"
        >
          <div
            v-for="step in recognitionStepOrder"
            :key="step"
            class="recognition-step"
            :class="`is-${recognitionSteps[step].status}`"
            :aria-current="recognitionSteps[step].status === 'running' ? 'step' : undefined"
          >
            <span class="recognition-step__index">{{ step === 'barcode' ? '01' : '02' }}</span>
            <span class="recognition-step__body">
              <strong>{{ stepLabel(step) }}</strong>
              <small>{{ stepStatusLabel(step) }}</small>
            </span>
          </div>
        </div>
        <button
          v-if="ocrMode !== 'barcode'"
          type="button"
          class="report-form__ocr-btn"
          :disabled="!ocrFiles[0] || ocrLoading"
          :aria-busy="ocrLoading"
          @click="runRecognition"
        >
          {{ ocrLoading ? report.scanRunning : report.scanAgain }}
        </button>
        <div v-if="recognitionInfo" class="report-form__ocr-info" role="status">
          <span class="report-form__ocr-info-label">{{ report.recognitionSource }}：</span>
          <strong>{{ sourceLabel(recognitionInfo.source) }}</strong>
          <span v-if="recognitionInfo.error" class="report-form__ocr-info-error">
            {{ errorLabel(recognitionInfo.error) }}
          </span>
        </div>
      </section>

      <section class="report-form__section">
        <header class="report-form__heading">
          <h3 class="report-form__title">2 · {{ report.sectionMeta_ }}</h3>
        </header>

        <div class="report-form__type" role="radiogroup" :aria-label="report.fieldTypeLabel">
          <button
            v-for="t in availableTypes"
            :key="t"
            type="button"
            role="radio"
            :aria-checked="type === t"
            class="type-chip"
            :class="{ 'is-active': type === t }"
            @click="setType(t)"
          >{{ typeLabel(t) }}</button>
        </div>

        <FormField
          v-model="identifier"
          :label="typeLabel(type)"
          :placeholder="typePlaceholder(type)"
          :error="errors.identifier"
          @update:modelValue="onIdentifierInput"
        />
        <FormField v-model="title" :label="report.fieldTitle" :error="errors.title" />
        <FormField v-model="author" :label="report.fieldAuthor" :error="errors.author" />
        <FormField
          v-model="description"
          :label="report.fieldDescription"
          multiline
          :placeholder="report.fieldDescriptionPlaceholder"
          :error="errors.description"
        />
      </section>

      <section class="report-form__section">
        <header class="report-form__heading">
          <h3 class="report-form__title">3 · {{ report.sectionAttach }}</h3>
        </header>
        <FileUploader
          :files="coverFile"
          :multiple="false"
          accept="image/jpeg,image/png,image/webp"
          :label="report.fieldCover"
          @update:files="onCoverFile"
        />
        <FileUploader
          :files="evidenceFiles"
          :multiple="true"
          :max-size="50 * 1024 * 1024"
          accept="image/*,video/mp4"
          :label="report.fieldEvidence"
          @update:files="onEvidenceFiles"
        />
      </section>

      <div v-if="formError" class="form-error" role="alert">
        <span class="form-error__icon" aria-hidden="true">!</span>
        <span>{{ formError }}</span>
      </div>

      <button type="submit" class="report-form__submit" :disabled="submitting">
        {{ submitting ? report.submitting : report.submit }}
      </button>
    </form>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { createReport } from '@/api/reports';
import {
  IDENTIFIER_TYPE_LABEL,
  IDENTIFIER_TYPE_PLACEHOLDER,
  type IdentifierType,
} from '@/api/identifiers';
import {
  recognizeIdentifier,
  type RecognitionProgress,
  type RecognitionStep,
  type RecognitionStepStatus,
} from '@/identifier';
import { applyRecognitionProgress } from '@/identifier/form';
import { useFingerprintStore } from '@/stores/fingerprint';
import { report } from '@/i18n/zh';
import SectionHeader from '@/components/SectionHeader.vue';
import FormField from '@/components/FormField.vue';
import FileUploader from '@/components/FileUploader.vue';
import CameraCapture from '@/components/CameraCapture.vue';
import BarcodeScanner from '@/components/BarcodeScanner.vue';

const router = useRouter();
const fpStore = useFingerprintStore();

const availableTypes: IdentifierType[] = ['isbn', 'issn'];
const type = ref<IdentifierType>('isbn');
const identifier = ref('');
const title = ref('');
const author = ref('');
const description = ref('');
type OcrMode = 'upload' | 'barcode' | 'camera';
type StepViewStatus = 'pending' | RecognitionStepStatus;
interface StepViewState {
  status: StepViewStatus;
  error?: string;
}
const recognitionStepOrder: RecognitionStep[] = ['barcode', 'ocr'];
const ocrMode = ref<OcrMode>('upload');
const ocrFiles = ref<File[]>([]);
const coverFile = ref<File[]>([]);
const evidenceFiles = ref<File[]>([]);
const ocrLoading = ref(false);
const submitting = ref(false);
const formError = ref<string | null>(null);
const recognitionInfo = ref<{ source: string; error?: string } | null>(null);
const recognitionSteps = reactive<Record<RecognitionStep, StepViewState>>({
  barcode: { status: 'pending' },
  ocr: { status: 'pending' },
});
let recognitionRunId = 0;

function sourceLabel(s: string): string {
  if (s === 'barcode') return report.sourceBarcode;
  if (s === 'ocr') return report.sourceOcr;
  return report.sourceNone;
}
function errorLabel(e?: string): string {
  if (e === 'imageTooBlurry') return report.imageTooBlurry;
  if (e === 'noMatch' || e === 'failed') return report.noMatch;
  return '';
}
function modeLabel(m: OcrMode): string {
  if (m === 'upload') return report.ocrModeUpload;
  if (m === 'barcode') return report.ocrModeBarcode;
  return report.ocrModeCamera;
}
function modeTip(m: OcrMode): string {
  if (m === 'upload') return report.tipUpload;
  if (m === 'barcode') return report.tipBarcode;
  return report.tipCamera;
}
function stepLabel(step: RecognitionStep): string {
  return step === 'barcode' ? report.recognitionStepBarcode : report.recognitionStepOcr;
}
function stepStatusLabel(step: RecognitionStep): string {
  const state = recognitionSteps[step];
  if (state.status === 'pending') return report.recognitionPending;
  if (state.status === 'running') return report.recognitionRunning;
  if (state.status === 'matched') return report.recognitionMatched;
  if (state.status === 'failed') {
    return step === 'barcode' ? report.recognitionFailedContinue : report.recognitionFailed;
  }
  return step === 'barcode' ? report.recognitionNoMatchContinue : report.recognitionNoMatch;
}

const errors = reactive<Record<string, string>>({
  identifier: '',
  title: '',
  author: '',
  description: '',
});

function typeLabel(t: IdentifierType): string {
  return IDENTIFIER_TYPE_LABEL[t];
}

function typePlaceholder(t: IdentifierType): string {
  return IDENTIFIER_TYPE_PLACEHOLDER[t];
}

function currentFields() {
  return {
    type: type.value,
    identifier: identifier.value,
    title: title.value,
    author: author.value,
    description: description.value,
  };
}

function applyFields(fields: ReturnType<typeof currentFields>) {
  type.value = fields.type;
  identifier.value = fields.identifier;
  title.value = fields.title;
  author.value = fields.author;
  description.value = fields.description;
}

function resetRecognitionState() {
  recognitionRunId += 1;
  recognitionSteps.barcode = { status: 'pending' };
  recognitionSteps.ocr = { status: 'pending' };
  recognitionInfo.value = null;
  ocrLoading.value = false;
}

function setType(t: IdentifierType) {
  if (type.value === t) return;
  type.value = t;
  identifier.value = '';
  errors.identifier = '';
  recognitionInfo.value = null;
}

function setOcrMode(m: OcrMode) {
  if (ocrMode.value === m) return;
  ocrMode.value = m;
  ocrFiles.value = [];
  resetRecognitionState();
}

function onOCRFiles(files: File[]) {
  ocrFiles.value = files;
  resetRecognitionState();
  if (files[0]) void runRecognition();
}

function onIdentifierInput() {
  recognitionInfo.value = null;
}
function onCameraFile(file: File | null) {
  ocrFiles.value = file ? [file] : [];
  resetRecognitionState();
  if (file) void runRecognition();
}
function onBarcodeIdentified(payload: { isbn?: string; issn?: string; type: 'isbn' | 'issn' }) {
  if (payload.isbn) {
    type.value = 'isbn';
    identifier.value = payload.isbn;
  } else if (payload.issn) {
    type.value = 'issn';
    identifier.value = payload.issn;
  }
  recognitionInfo.value = { source: 'barcode' };
}
function onCoverFile(files: File[]) {
  coverFile.value = files;
}
function onEvidenceFiles(files: File[]) {
  evidenceFiles.value = files;
}

function handleProgress(runId: number, progress: RecognitionProgress) {
  if (runId !== recognitionRunId) return;
  recognitionSteps[progress.step] = {
    status: progress.status,
    error: progress.error,
  };
  applyFields(applyRecognitionProgress(currentFields(), progress));
}

async function runRecognition() {
  const image = ocrFiles.value[0];
  if (!image || ocrLoading.value) return;
  const runId = ++recognitionRunId;
  recognitionSteps.barcode = { status: 'pending' };
  recognitionSteps.ocr = { status: 'pending' };
  ocrLoading.value = true;
  recognitionInfo.value = null;
  try {
    const result = await recognizeIdentifier(image, {
      onProgress: (progress) => handleProgress(runId, progress),
    });
    if (runId !== recognitionRunId) return;
    recognitionInfo.value = {
      source: result.source,
      error: result.error,
    };
  } finally {
    if (runId === recognitionRunId) ocrLoading.value = false;
  }
}

function validate(): boolean {
  const v = identifier.value.replace(/[-\s]/g, '');
  let valid = false;
  if (type.value === 'isbn') {
    valid = /^(?:\d{9}[\dX]|\d{13})$/.test(v);
  } else {
    valid = /^\d{7}[\dX]$/.test(v);
  }
  errors.identifier = valid ? '' : report.errors.identifier;
  errors.title = title.value.trim() ? '' : report.errors.titleRequired;
  errors.author = author.value.trim() ? '' : report.errors.authorRequired;
  errors.description = description.value.length >= 10 ? '' : report.errors.descriptionMin;
  return !errors.identifier && !errors.title && !errors.author && !errors.description;
}

async function onSubmit() {
  formError.value = null;
  if (!validate()) return;
  submitting.value = true;
  try {
    const fp = await fpStore.ensure();
    const { data } = await createReport({
      type: type.value,
      identifier: identifier.value,
      title: title.value,
      author: author.value,
      description: description.value,
      fingerprint: fp,
      cover: coverFile.value[0],
      evidences: evidenceFiles.value,
    });
    const respId = (
      data as { identifier: { type: IdentifierType; identifier: string } }
    ).identifier;
    router.push(`/identifiers/${respId.type}/${encodeURIComponent(respId.identifier)}`);
  } catch (e: unknown) {
    const status = (e as { response?: { status?: number } })?.response?.status;
    formError.value = status === 429 ? report.errors.rateLimited : report.errors.submitFailed;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.report-form { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
.report-form__ocr-btn {
  margin-top: 12px;
  background: var(--ink-deep);
  color: #fff;
  border: none;
  padding: 10px 18px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.14em;
  border-radius: 999px;
  cursor: pointer;
}
.report-form__ocr-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.recognition-steps {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.recognition-step {
  display: flex;
  gap: 12px;
  align-items: center;
  min-height: 64px;
  padding: 12px 14px;
  border: 1px solid var(--surface-rule);
  border-radius: 8px;
  background: var(--surface-tray);
  color: var(--ink-soft);
  transition: border-color 180ms ease, background 180ms ease, color 180ms ease;
}
.recognition-step.is-running {
  border-color: var(--quarantine-ok);
  background: rgba(33, 89, 68, 0.08);
  color: var(--ink-deep);
}
.recognition-step.is-matched { border-color: var(--quarantine-ok); }
.recognition-step.is-failed,
.recognition-step.is-noMatch { border-color: var(--quarantine-warn); }
.recognition-step__index {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
}
.recognition-step__body { display: grid; gap: 4px; }
.recognition-step__body strong { font-family: var(--font-cn); font-size: 13px; }
.recognition-step__body small { font-family: var(--font-cn); font-size: 11px; color: var(--ink-soft); }
.report-form__ocr-info {
  margin-top: 10px;
  font-family: var(--font-cn);
  font-size: 12px;
  color: var(--ink-soft);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: baseline;
}
.report-form__ocr-info strong {
  color: var(--quarantine-ok);
  font-weight: 500;
}
.report-form__ocr-info-error {
  color: var(--quarantine-warn);
  margin-left: 4px;
}
.report-form__type {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.report-form__ocr-mode {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.report-form__ocr-tip {
  font-family: var(--font-cn);
  font-size: 12px;
  color: var(--ink-soft);
  background: var(--surface-tray);
  border-left: 3px solid var(--quarantine-ok);
  padding: 8px 12px;
  border-radius: 4px;
  margin: 0 0 12px;
  line-height: 1.6;
}
.type-chip {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  padding: 6px 14px;
  border: 1px solid var(--surface-rule);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ink-soft);
  cursor: pointer;
  text-transform: uppercase;
}
.type-chip:hover {
  color: var(--quarantine-ok);
  border-color: var(--quarantine-ok);
}
.type-chip.is-active {
  background: var(--quarantine-ok);
  color: #fff;
  border-color: var(--quarantine-ok);
}
@media (max-width: 600px) {
  .recognition-steps { grid-template-columns: 1fr; }
}
</style>
