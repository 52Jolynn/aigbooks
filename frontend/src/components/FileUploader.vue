<template>
  <div
    class="file-uploader"
    :class="{ 'is-dragging': dragging, 'is-error': error }"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
  >
    <input
      ref="inputEl"
      type="file"
      :multiple="multiple"
      :accept="accept"
      style="display:none"
      @change="onChange"
    />
    <div class="file-uploader__inner" @click="inputEl?.click()">
      <span class="file-uploader__label">{{ label }}</span>
      <span class="file-uploader__hint">{{ accept }} · max {{ Math.round(maxSize / 1024 / 1024) }}MB</span>
    </div>
    <p v-if="error" class="file-uploader__error">{{ error }}</p>
    <ul v-if="files.length" class="file-uploader__list">
      <li v-for="(f, i) in files" :key="i">
        {{ f.name }} ({{ Math.round(f.size / 1024) }}KB)
        <button type="button" @click="remove(i)">×</button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = withDefaults(
  defineProps<{
    multiple?: boolean;
    accept?: string;
    maxSize?: number;
    label?: string;
  }>(),
  { multiple: false, accept: 'image/*', maxSize: 20 * 1024 * 1024, label: 'Drag & drop or click' },
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
      error.value = `${f.name} 超过 ${Math.round(props.maxSize / 1024 / 1024)}MB 上限`;
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
.file-uploader {
  border: 2px dashed var(--paper-shadow);
  background: var(--paper);
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.file-uploader.is-dragging { border-color: var(--stamp-red); background: var(--alert-bg); }
.file-uploader.is-error { border-color: var(--stamp-red); }
.file-uploader__label {
  display: block;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.file-uploader__hint {
  display: block;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faint);
}
.file-uploader__error {
  color: var(--stamp-red);
  font-size: 12px;
  margin-top: 8px;
  font-family: var(--font-mono);
}
.file-uploader__list {
  list-style: none;
  padding: 0;
  margin-top: 12px;
  text-align: left;
}
.file-uploader__list li {
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 4px 0;
  display: flex;
  justify-content: space-between;
}
</style>
