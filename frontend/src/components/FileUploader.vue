<template>
  <div
    class="file-uploader"
    :class="{ 'is-dragging': dragging, 'is-error': error, 'file-uploader--camera': !!capture }"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
  >
    <input
      ref="inputEl"
      type="file"
      :multiple="multiple"
      :accept="accept"
      :capture="capture || undefined"
      class="file-uploader__native"
      :class="{ 'file-uploader__native--camera': !!capture }"
      @change="onChange"
    />
    <button type="button" class="file-uploader__trigger" @click="inputEl?.click()">
      <span>{{ label }}</span>
      <span class="file-uploader__meta">
        {{ accept }} {{ report.uploadMax(Math.round(maxSize / 1024 / 1024)) }}
      </span>
    </button>
    <p v-if="error" class="form-field__error">{{ error }}</p>
    <ul v-if="files.length" class="file-uploader__files">
      <li v-for="(f, i) in files" :key="i" class="file-uploader__file">
        <span>{{ f.name }} {{ report.uploadSize(Math.round(f.size / 1024)) }}</span>
        <button
          type="button"
          class="file-uploader__remove"
          :aria-label="file.ariaRemove"
          @click="remove(i)"
        >✕</button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { file, report } from '@/i18n/zh';

const props = withDefaults(
  defineProps<{
    multiple?: boolean;
    accept?: string;
    maxSize?: number;
    label?: string;
    capture?: 'environment' | 'user';
  }>(),
  { multiple: false, accept: 'image/*', maxSize: 20 * 1024 * 1024, label: report.uploadHint },
);
const emit = defineEmits<{ 'update:files': [File[]] }>();

const inputEl = ref<HTMLInputElement | null>(null);
const dragging = ref(false);
const files = ref<File[]>([]);
const error = ref<string | null>(null);

function addFiles(list: FileList | null) {
  if (!list) return;
  for (const f of Array.from(list)) {
    if (f.size > props.maxSize) {
      error.value = file.tooLarge(f.name, Math.round(props.maxSize / 1024 / 1024));
      continue;
    }
    files.value.push(f);
  }
  emit('update:files', files.value);
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  addFiles(e.dataTransfer?.files ?? null);
}

function onChange(e: Event) {
  const target = e.target as HTMLInputElement;
  addFiles(target.files);
  target.value = '';
}

function remove(i: number) {
  files.value.splice(i, 1);
  emit('update:files', files.value);
}
</script>

<style scoped>
.file-uploader--camera {
  position: relative;
}
.file-uploader__native {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.file-uploader__native--camera {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  clip: auto;
  opacity: 0;
  cursor: pointer;
  z-index: 2;
}
.file-uploader__remove {
  position: relative;
  z-index: 3;
}
</style>