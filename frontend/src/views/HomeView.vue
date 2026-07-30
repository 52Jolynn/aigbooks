<template>
  <main class="ledger">
    <SectionHeader num="§ 01 —" title="Latest Filings" :meta="`${reports.length} most recent · ordered by gravity`" />
    <FeaturedReport v-if="reports[0]" :report="reports[0]" />
    <ReportsGrid v-if="reports.length > 1" :reports="reports.slice(1, 19)" />
    <div
      v-if="loading"
      style="text-align:center; padding:32px; font-family:var(--font-mono); color:var(--ink-faint)"
    >
      Loading...
    </div>
    <div
      v-else-if="!reports.length"
      style="text-align:center; padding:64px 32px; font-family:var(--font-display); font-style:italic; color:var(--ink-soft)"
    >
      No reports filed yet.
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRecentStore } from '@/stores/reports';
import SectionHeader from '@/components/SectionHeader.vue';
import FeaturedReport from '@/components/FeaturedReport.vue';
import ReportsGrid from '@/components/ReportsGrid.vue';

const store = useRecentStore();
const reports = computed(() => store.reports);
const loading = computed(() => store.loading);

onMounted(() => store.refresh());
</script>
