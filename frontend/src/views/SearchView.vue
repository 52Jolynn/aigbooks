<template>
  <main class="ledger">
    <SectionHeader
      :num="search.sectionNum"
      :title="search.sectionTitle"
      :meta="search.sectionMeta(q)"
    />

    <section class="search-station" :aria-label="search.stationLabel">
      <div class="search-station__stamp">
        <span aria-hidden="true">◇</span>
        {{ search.cardLabel }}
      </div>
      <SearchBox v-model="q" @search="onSearch" />
      <div class="search-station__fields">
        <span class="search-station__fields-label">{{ search.field.label }}</span>
        <div class="search-station__chips" role="radiogroup" :aria-label="search.field.label">
          <button
            v-for="f in fields"
            :key="f.value"
            type="button"
            role="radio"
            :aria-checked="activeField === f.value"
            class="search-chip"
            :class="{ 'is-active': activeField === f.value }"
            @click="setField(f.value)"
          >{{ f.label }}</button>
        </div>
      </div>
    </section>

    <section class="search-archive">
      <header class="search-archive__head">
        <span class="search-archive__title">{{ search.archiveLabel }}</span>
        <span class="search-archive__rule" aria-hidden="true"></span>
        <span class="search-archive__count">{{ search.archiveCount(results.length) }}</span>
      </header>

      <ReportsGrid v-if="results.length" :reports="results" />
      <div v-else class="search-empty-archive">
        <div class="search-empty-archive__stamp" aria-hidden="true">◇ EMPTY · 00</div>
        <p class="search-empty-archive__text">{{ emptyText }}</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { searchReports, type SearchField } from '@/api/search';
import type { ReportOut } from '@/api/identifiers';
import { consoleMessages, search } from '@/i18n/zh';
import SectionHeader from '@/components/SectionHeader.vue';
import ReportsGrid from '@/components/ReportsGrid.vue';
import SearchBox from '@/components/SearchBox.vue';

const route = useRoute();
const router = useRouter();
const q = ref<string>((route.query.q as string) ?? '');
const activeField = ref<SearchField>((route.query.field as SearchField) || 'all');
const results = ref<ReportOut[]>([]);

type FieldItem = { value: SearchField; label: string };

const fields: FieldItem[] = [
  { value: 'all', label: search.field.all },
  { value: 'identifier', label: search.field.identifier },
  { value: 'title', label: search.field.title },
  { value: 'author', label: search.field.author },
  { value: 'description', label: search.field.description },
];

const emptyText = computed(() => (q.value ? search.empty(q.value) : search.prompt));

async function doSearch(query: string, field: SearchField) {
  if (!query.trim()) {
    results.value = [];
    return;
  }
  try {
    const data = await searchReports(query, field);
    results.value = data.reports;
  } catch (e) {
    console.error(consoleMessages.searchFailed, e);
    results.value = [];
  }
}

function syncUrl() {
  router.replace({
    query: {
      ...route.query,
      q: q.value || undefined,
      field: activeField.value === 'all' ? undefined : activeField.value,
    },
  });
}

function onSearch(query: string) {
  syncUrl();
  void doSearch(query, activeField.value);
}

function setField(field: SearchField) {
  if (activeField.value === field) return;
  activeField.value = field;
  syncUrl();
  void doSearch(q.value, field);
}

watch(
  () => route.query,
  (next) => {
    const newQ = (next.q as string) ?? '';
    const newField = ((next.field as SearchField) || 'all') as SearchField;
    if (newQ !== q.value) q.value = newQ;
    if (newField !== activeField.value) activeField.value = newField;
    void doSearch(q.value, activeField.value);
  },
  { immediate: true },
);
</script>

<style scoped>
.search-station {
  position: relative;
  border: 1px solid var(--surface-rule);
  border-left: 4px solid var(--quarantine-ok);
  background: var(--surface);
  padding: 28px 32px 24px;
  margin-bottom: 36px;
}

.search-station__stamp {
  position: absolute;
  top: -14px;
  left: 22px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: var(--quarantine-ok-soft);
  border: 1px solid var(--quarantine-ok);
  color: var(--ink-deep);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  border-radius: var(--radius-stamp);
}

.search-station__fields {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed var(--surface-rule);
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.search-station__fields-label {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--ink-soft);
  text-transform: uppercase;
}

.search-station__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.search-chip {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.14em;
  padding: 6px 14px;
  border: 1px solid var(--surface-rule);
  border-radius: var(--radius-stamp);
  background: rgba(255, 255, 255, 0.92);
  color: var(--ink-soft);
  cursor: pointer;
  text-transform: uppercase;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background var(--transition-fast);
}

.search-chip:hover {
  color: var(--quarantine-ok);
  border-color: var(--quarantine-ok);
}

.search-chip.is-active {
  background: var(--quarantine-ok);
  color: #fff;
  border-color: var(--quarantine-ok);
}

.search-archive {
  margin-top: 8px;
}

.search-archive__head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}

.search-archive__title {
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: 0.22em;
  color: var(--quarantine-ok);
  text-transform: uppercase;
}

.search-archive__rule {
  flex: 1;
  height: 1px;
  background: var(--surface-rule);
}

.search-archive__count {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  color: var(--ink-soft);
  text-transform: uppercase;
}

.search-empty-archive {
  border: 1px dashed var(--surface-rule);
  background: var(--surface-tray);
  padding: 56px 32px;
  text-align: center;
  position: relative;
}

.search-empty-archive__stamp {
  display: inline-block;
  margin-bottom: 14px;
  padding: 4px 12px;
  border: 1px solid var(--surface-rule);
  border-radius: var(--radius-stamp);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--ink-soft);
}

.search-empty-archive__text {
  font-family: var(--font-cn-display);
  font-style: italic;
  font-size: 18px;
  color: var(--ink-soft);
}

@media (max-width: 720px) {
  .search-station {
    padding: 24px 20px 18px;
  }
}
</style>