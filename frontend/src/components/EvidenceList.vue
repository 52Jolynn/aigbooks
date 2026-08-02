<template>
  <div v-if="evidences.length" class="evidence-list" role="list">
    <button
      v-for="ev in evidences"
      :key="ev.id"
      class="evidence-list__item"
      type="button"
      :aria-label="`${kindLabel(ev.file_kind)}: ${basename(ev.file_path)}`"
      @click="openPreview(ev)"
    >
      <img
        v-if="ev.file_kind === 'image'"
        class="evidence-list__media"
        :src="`/evidence/${ev.file_path}`"
        :alt="detail.evidenceAlt"
        loading="lazy"
      />
      <div
        v-else-if="ev.file_kind === 'video'"
        class="evidence-list__thumb evidence-list__thumb--video"
        :style="`--thumb-bg: ${posterTint(ev)}`"
      >
        <video
          class="evidence-list__media"
          :src="`/evidence/${ev.file_path}`"
          preload="metadata"
          muted
        />
        <span class="evidence-list__badge">▶ VIDEO</span>
      </div>
      <div
        v-else-if="ev.file_kind === 'audio'"
        class="evidence-list__thumb evidence-list__thumb--audio"
      >
        <svg
          class="evidence-list__glyph"
          viewBox="0 0 24 24"
          aria-hidden="true"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path d="M9 9v6l5-3z" fill="currentColor" stroke="none" />
          <path d="M3 12h2M19 12h2" />
          <path d="M5 8v8M7 6v12M11 5v14M13 5v14M17 8v8M21 10v4" />
        </svg>
        <span class="evidence-list__badge">♪ AUDIO</span>
      </div>
      <div v-else class="evidence-list__thumb evidence-list__thumb--doc">
        <span class="evidence-list__badge">{{ kindLabel(ev.file_kind) }}</span>
        <span class="evidence-list__name">{{ basename(ev.file_path) }}</span>
      </div>
    </button>
  </div>

  <Teleport to="body">
    <dialog
      ref="dialog"
      class="evidence-preview"
      @cancel="preview = null"
      @click="onBackdrop"
    >
      <div class="evidence-preview__frame" @click.stop>
        <header class="evidence-preview__head">
          <span class="evidence-preview__case">
            {{ preview ? kindLabel(preview.file_kind) : '' }}
          </span>
          <span class="evidence-preview__name">{{ preview?.file_path }}</span>
          <button
            class="evidence-preview__close"
            type="button"
            aria-label="关闭"
            @click="closePreview"
          >
            ×
          </button>
        </header>
        <figure class="evidence-preview__body">
          <img
            v-if="preview?.file_kind === 'image'"
            :src="`/evidence/${preview.file_path}`"
            :alt="detail.evidenceAlt"
          />
          <video
            v-else-if="preview?.file_kind === 'video'"
            :src="`/evidence/${preview.file_path}`"
            controls
            autoplay
          ></video>
          <audio
            v-else-if="preview?.file_kind === 'audio'"
            :src="`/evidence/${preview.file_path}`"
            controls
            autoplay
          ></audio>
          <div v-else class="evidence-preview__doc">
            <p class="evidence-preview__doc-path">{{ preview?.file_path }}</p>
            <a
              v-if="preview"
              class="evidence-preview__doc-link"
              :href="`/evidence/${preview.file_path}`"
              target="_blank"
              rel="noopener"
            >
              在新窗口打开 ↓
            </a>
          </div>
        </figure>
      </div>
    </dialog>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { EvidenceOut } from '@/api/identifiers';
import { detail } from '@/i18n/zh';

defineProps<{ evidences: EvidenceOut[] }>();

const preview = ref<EvidenceOut | null>(null);
const dialog = ref<HTMLDialogElement | null>(null);

const KIND_LABELS: Record<string, string> = {
  image: 'IMAGE',
  video: 'VIDEO',
  audio: 'AUDIO',
  application: 'DOC',
  text: 'DOC',
};

function kindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? 'FILE';
}

function basename(p: string): string {
  const i = p.lastIndexOf('/');
  return i >= 0 ? p.slice(i + 1) : p;
}

function posterTint(ev: EvidenceOut): string {
  return ev.mime_type?.startsWith('video') ? '#1a2622' : '#2a342f';
}

function openPreview(ev: EvidenceOut) {
  preview.value = ev;
  dialog.value?.showModal();
}

function closePreview() {
  dialog.value?.close();
  preview.value = null;
}

function onBackdrop(e: MouseEvent) {
  if (e.target === dialog.value) closePreview();
}
</script>
