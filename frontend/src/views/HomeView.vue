<template>
  <main class="ledger">
    <SectionHeader
      :num="home.sectionNum"
      :title="home.sectionTitle"
      :meta="home.sectionMeta(reports.length)"
    />

    <section class="disclaimer" aria-label="重要声明">
      <span class="disclaimer__icon" aria-hidden="true">✦</span>
      <div>
        <p class="disclaimer__title">{{ disclaimer.title }}</p>
        <p>{{ disclaimer.body }}</p>
      </div>
    </section>

    <FeaturedReport v-if="reports[0]" :report="reports[0]" />
    <ReportsGrid v-if="reports.length > 1" :reports="reports.slice(1, 19)" />

    <div v-if="loading" class="ledger__loading">{{ home.loading }}</div>
    <div v-else-if="!reports.length" class="ledger__empty">{{ home.empty }}</div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRecentStore } from '@/stores/reports';
import { disclaimer, home } from '@/i18n/zh';
import SectionHeader from '@/components/SectionHeader.vue';
import FeaturedReport from '@/components/FeaturedReport.vue';
import ReportsGrid from '@/components/ReportsGrid.vue';

const store = useRecentStore();
const reports = computed(() => store.reports);
const loading = computed(() => store.loading);

onMounted(() => store.refresh());
</script>

<style scoped>
.ledger__loading,
.ledger__empty {
  text-align: center;
  padding: 64px 32px;
  font-family: var(--font-cn);
  color: var(--ink-faint);
  letter-spacing: 0.04em;
}
.ledger__empty {
  font-family: var(--font-cn-display);
  font-style: italic;
  color: var(--ink-soft);
  font-size: 18px;
}
</style>