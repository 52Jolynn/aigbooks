<template>
  <div class="evidence-list">
    <div v-for="ev in evidences" :key="ev.id" class="evidence-list__item">
      <img v-if="ev.file_kind === 'image'" :src="`/evidence/${ev.file_path}`" :alt="ev.mime_type ?? ''" />
      <video v-else-if="ev.file_kind === 'video'" :src="`/evidence/${ev.file_path}`" controls></video>
      <span v-else>{{ ev.file_path }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EvidenceOut } from '@/api/books';
defineProps<{ evidences: EvidenceOut[] }>();
</script>

<style scoped>
.evidence-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.evidence-list__item img,
.evidence-list__item video {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border: 1px solid var(--rule);
}
</style>
