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
        <FileUploader
          :files="ocrFiles"
          accept="image/*"
          :label="report.scanLabel"
          @update:files="onOCRFiles"
        />
        <button
          v-if="ocrFiles[0]"
          type="button"
          class="report-form__ocr-btn"
          :disabled="ocrLoading"
          @click="runOCR"
        >
          {{ ocrLoading ? report.scanRunning : report.scanAction }}
        </button>
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
import { recognizeText } from '@/ocr';
import { useFingerprintStore } from '@/stores/fingerprint';
import { report } from '@/i18n/zh';
import SectionHeader from '@/components/SectionHeader.vue';
import FormField from '@/components/FormField.vue';
import FileUploader from '@/components/FileUploader.vue';

const router = useRouter();
const fpStore = useFingerprintStore();

const availableTypes: IdentifierType[] = ['isbn', 'issn'];
const type = ref<IdentifierType>('isbn');
const identifier = ref('');
const title = ref('');
const author = ref('');
const description = ref('');
const ocrFiles = ref<File[]>([]);
const coverFile = ref<File[]>([]);
const evidenceFiles = ref<File[]>([]);
const ocrLoading = ref(false);
const submitting = ref(false);
const formError = ref<string | null>(null);

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

function setType(t: IdentifierType) {
  if (type.value === t) return;
  type.value = t;
  identifier.value = '';
  errors.identifier = '';
}

function onOCRFiles(files: File[]) {
  ocrFiles.value = files;
}
function onCoverFile(files: File[]) {
  coverFile.value = files;
}
function onEvidenceFiles(files: File[]) {
  evidenceFiles.value = files;
}

async function runOCR() {
  if (!ocrFiles.value[0]) return;
  ocrLoading.value = true;
  try {
    const result = await recognizeText(ocrFiles.value[0]);
    if (result.isbn) {
      type.value = 'isbn';
      identifier.value = result.isbn;
    } else if (result.issn) {
      type.value = 'issn';
      identifier.value = result.issn;
    }
    if (result.title) title.value = result.title;
    if (result.author) author.value = result.author;
  } finally {
    ocrLoading.value = false;
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

.report-form__type {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
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
</style>