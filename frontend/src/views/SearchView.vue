<template>
  <main class="ledger">
    <SectionHeader
      :num="search.sectionNum"
      :title="search.sectionTitle"
      :meta="search.sectionMeta(q)"
    />
    <div class="search-wrap">
      <SearchBox v-model="q" @search="onSearch" />
    </div>
    <ReportsGrid v-if="results.length" :reports="results" />
    <div v-else-if="q" class="search-empty">{{ search.empty(q) }}</div>
    <div v-else class="search-empty">{{ search.prompt }}</div>
  </main>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { searchReports } from '@/api/search';
import type { ReportOut } from '@/api/books';
import { consoleMessages, search } from '@/i18n/zh';
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
    console.error(consoleMessages.searchFailed, e);
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

<style scoped>
.search-wrap {
  text-align: center;
  margin-bottom: 32px;
}
.search-empty {
  text-align: center;
  padding: 64px 32px;
  font-family: var(--font-cn-display);
  font-style: italic;
  color: var(--ink-soft);
  font-size: 18px;
}
</style>