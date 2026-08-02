<template>
  <div v-if="evidences.length" class="evidence-list">
    <div v-for="ev in evidences" :key="ev.id" class="evidence-list__item">
      <img
        v-if="ev.file_kind === 'image'"
        :src="`/evidence/${ev.file_path}`"
        :alt="detail.evidenceAlt"
      />
      <video
        v-else-if="ev.file_kind === 'video'"
        :src="`/evidence/${ev.file_path}`"
        controls
      ></video>
      <span v-else class="evidence-list__fallback">{{ ev.file_path }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EvidenceOut } from '@/api/identifiers';
import { detail } from '@/i18n/zh';

defineProps<{ evidences: EvidenceOut[] }>();
</script>