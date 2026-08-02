<template>
  <section class="reports-grid">
    <div
      v-for="(r, i) in reports"
      :key="r.id"
      :style="{ animationDelay: `${0.05 * (i + 1)}s` }"
    >
      <ReportCard :report="r" :index="i" />
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ReportOut } from '@/api/identifiers';
import ReportCard from './ReportCard.vue';

defineProps<{ reports: ReportOut[] }>();
</script>