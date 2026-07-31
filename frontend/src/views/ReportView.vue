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
        <FormField
          v-model="isbn"
          :label="report.fieldIsbn"
          placeholder="978-7-100-12345-6"
          :error="errors.isbn"
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
import { recognizeText } from '@/ocr';
import { useFingerprintStore } from '@/stores/fingerprint';
import { report } from '@/i18n/zh';
import SectionHeader from '@/components/SectionHeader.vue';
import FormField from '@/components/FormField.vue';
import FileUploader from '@/components/FileUploader.vue';

const router = useRouter();
const fpStore = useFingerprintStore();

const isbn = ref('');
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
  isbn: '',
  title: '',
  author: '',
  description: '',
});

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
    if (result.isbn) isbn.value = result.isbn;
    if (result.title) title.value = result.title;
    if (result.author) author.value = result.author;
  } finally {
    ocrLoading.value = false;
  }
}

function validate(): boolean {
  errors.isbn = /^[0-9-]{10,17}$/.test(isbn.value) ? '' : report.errors.isbn;
  errors.title = title.value.trim() ? '' : report.errors.titleRequired;
  errors.author = author.value.trim() ? '' : report.errors.authorRequired;
  errors.description = description.value.length >= 10 ? '' : report.errors.descriptionMin;
  return !errors.isbn && !errors.title && !errors.author && !errors.description;
}

async function onSubmit() {
  formError.value = null;
  if (!validate()) return;
  submitting.value = true;
  try {
    const fp = await fpStore.ensure();
    const { data } = await createReport({
      isbn: isbn.value,
      title: title.value,
      author: author.value,
      description: description.value,
      fingerprint: fp,
      cover: coverFile.value[0],
      evidences: evidenceFiles.value,
    });
    const respIsbn = (data as { book: { isbn: string } }).book.isbn;
    router.push(`/books/${respIsbn}`);
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
</style>