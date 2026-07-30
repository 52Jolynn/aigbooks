<template>
  <main class="ledger">
    <SectionHeader
      num="§ 04 —"
      title="File a Report"
      meta="Anonymous · IP + fingerprint throttled · 5 per hour"
    />
    <form class="report-form" @submit.prevent="onSubmit">
      <div class="report-form__section">
        <h3>1 · OCR（可选）</h3>
        <FileUploader
          :files="ocrFiles"
          accept="image/*"
          label="Scan ISBN or book spine"
          @update:files="onOCRFiles"
        />
        <button
          v-if="ocrFiles[0]"
          type="button"
          class="report-form__ocr-btn"
          :disabled="ocrLoading"
          @click="runOCR"
        >
          {{ ocrLoading ? 'Recognizing…' : 'Run OCR' }}
        </button>
      </div>
      <div class="report-form__section">
        <h3>2 · Metadata</h3>
        <FormField v-model="isbn" label="ISBN" placeholder="978-7-100-12345-6" :error="errors.isbn" />
        <FormField v-model="title" label="Title" :error="errors.title" />
        <FormField v-model="author" label="Author" :error="errors.author" />
        <FormField
          v-model="description"
          label="Description"
          multiline
          placeholder="At least 10 characters…"
          :error="errors.description"
        />
      </div>
      <div class="report-form__section">
        <h3>3 · Attachments</h3>
        <FileUploader
          :files="coverFile"
          :multiple="false"
          accept="image/jpeg,image/png,image/webp"
          label="Cover (optional)"
          @update:files="onCoverFile"
        />
        <FileUploader
          :files="evidenceFiles"
          :multiple="true"
          accept="image/*,video/mp4"
          label="Evidence files (optional)"
          @update:files="onEvidenceFiles"
        />
      </div>
      <button type="submit" class="report-form__submit" :disabled="submitting">
        {{ submitting ? 'Filing…' : 'FILE REPORT' }}
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
  errors.isbn = /^[0-9-]{10,17}$/.test(isbn.value) ? '' : 'ISBN 格式不正确';
  errors.title = title.value.trim() ? '' : '书名必填';
  errors.author = author.value.trim() ? '' : '作者必填';
  errors.description = description.value.length >= 10 ? '' : '描述至少 10 字';
  return !errors.isbn && !errors.title && !errors.author && !errors.description;
}

async function onSubmit() {
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
    if (status === 429) alert('举报过于频繁，请稍后再试');
    else alert('提交失败，请重试');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.report-form { max-width: 720px; margin: 0 auto; }
.report-form__section { margin-bottom: 32px; }
.report-form__section h3 {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--ink);
  border-bottom: 1px solid var(--rule);
  padding-bottom: 4px;
  margin-bottom: 12px;
}
.report-form__ocr-btn {
  margin-top: 8px;
  background: var(--ink);
  color: var(--paper);
  border: none;
  padding: 8px 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.report-form__submit {
  width: 100%;
  background: var(--stamp-red);
  color: var(--paper);
  border: 3px solid var(--stamp-red-deep);
  padding: 18px;
  font-family: var(--font-display);
  font-variation-settings: "wght" 900;
  font-size: 28px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  transform: rotate(-1deg);
  cursor: pointer;
  transition: all 0.2s;
}
.report-form__submit:hover { transform: rotate(-1deg) scale(1.02); }
.report-form__submit:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
