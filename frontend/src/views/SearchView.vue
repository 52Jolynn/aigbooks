<template>
  <main class="ledger">
    <SectionHeader num="§ 02 —" title="Search the Dossier" :meta="`Query: ${q || '—'}`" />
    <div style="text-align:center; margin-bottom:32px">
      <SearchBox v-model="q" @search="onSearch" />
    </div>
    <ReportsGrid v-if="results.length" :reports="results" />
    <div
      v-else-if="q"
      style="text-align:center; padding:64px 32px; font-family:var(--font-display); font-style:italic; color:var(--ink-soft)"
    >
      No reports filed yet for "{{ q }}".
    </div>
    <div
      v-else
      style="text-align:center; padding:64px 32px; font-family:var(--font-display); font-style:italic; color:var(--ink-soft)"
    >
      Enter a keyword to search.
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { searchReports } from '@/api/search';
import type { ReportOut } from '@/api/books';
import SectionHeader from '@/components/SectionHeader.vue';
import ReportsGrid from '@/components/ReportsGrid.vue';
import SearchBox from '@/components/SearchBox.vue';

const route = useRoute();
const router = useRouter();
const q = ref<string>((route.query.q as string) ?? '');
const results = ref<ReportOut[]>([]);

async function doSearch(query: string) {
  if (!query.trim()) {
    results.value = [];
    return;
  }
  try {
    const data = await searchReports(query);
    results.value = data.reports;
  } catch (e) {
    console.error('Search failed:', e);
    results.value = [];
  }
}

function onSearch(query: string) {
  router.replace({ query: { q: query } });
  void doSearch(query);
}

watch(
  () => route.query.q,
  (newQ) => {
    q.value = (newQ as string) ?? '';
    void doSearch(q.value);
  },
  { immediate: true },
);
</script>
