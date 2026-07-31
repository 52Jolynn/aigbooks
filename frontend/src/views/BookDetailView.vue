<template>
  <main class="ledger">
    <div v-if="loading" class="state-loading">{{ detail.loading }}</div>
    <div v-else-if="error" class="state-error">{{ error }}</div>
    <div v-else-if="book" class="book-detail">
      <aside class="book-detail__meta">
        <div class="sample-bag">
          <div class="sample-bag__cover">
            <img
              v-if="book.cover_path"
              :src="`/covers/${book.cover_path}`"
              :alt="book.title"
            />
            <span v-else class="sample-bag__cover-fallback" aria-hidden="true">无</span>
            <span class="sample-bag__cover-corner sample-bag__cover-corner--bl">
              ISBN {{ book.isbn }}
            </span>
            <span class="sample-bag__cover-corner sample-bag__cover-corner--br">
              {{ earliestLabel }}
            </span>
          </div>
        </div>
        <h1 class="book-detail__title">{{ book.title }}</h1>
        <p class="book-detail__author">{{ book.author }}</p>
        <p class="book-detail__meta-line">ISBN {{ book.isbn }}</p>
        <Stamp :count="book.report_count" size="featured">
          {{ card.reportedCount(book.report_count) }}
        </Stamp>

        <div v-if="shouldWarn" class="book-detail__warning" role="note">
          <p class="book-detail__warning-title">{{ detail.warningTitle }}</p>
          <p>{{ detail.warningBody }}</p>
        </div>
      </aside>

      <section class="book-detail__reports">
        <SectionHeader
          :num="detail.sectionNum"
          :title="detail.sectionTitle"
          :meta="detail.sectionMeta(book.reports.length)"
        />
        <ul v-if="book.reports.length" class="report-timeline">
          <li v-for="r in book.reports" :key="r.id" class="report-timeline__item">
            <header class="report-timeline__head">
              <span class="report-timeline__case">{{ formatCaseNumber(r.id) }}</span>
              <span>{{ card.filedOn }} {{ r.created_at.slice(0, 10) }}</span>
              <span class="quarantine-stamp quarantine-stamp--ok">
                {{ r.evidences.length }} 份证据
              </span>
            </header>
            <p class="report-timeline__body">「{{ r.description }}」</p>
            <EvidenceList :evidences="r.evidences" />
            <footer class="report-timeline__footer">
              <VoteButton :report="r" />
            </footer>
          </li>
        </ul>
        <div v-else class="state-empty">{{ detail.empty }}</div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { getBookDetail, type BookDetailOut } from '@/api/books';
import { card, detail, formatCaseNumber } from '@/i18n/zh';
import SectionHeader from '@/components/SectionHeader.vue';
import Stamp from '@/components/Stamp.vue';
import VoteButton from '@/components/VoteButton.vue';
import EvidenceList from '@/components/EvidenceList.vue';

const route = useRoute();
const book = ref<BookDetailOut | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function load(isbn: string) {
  loading.value = true;
  error.value = null;
  try {
    book.value = await getBookDetail(isbn);
  } catch (e: unknown) {
    book.value = null;
    const status = (e as { response?: { status?: number } })?.response?.status;
    error.value = status === 404 ? detail.notFound : detail.loadFailed;
  } finally {
    loading.value = false;
  }
}

const earliestLabel = computed(() => {
  if (!book.value?.reports?.length) return '—';
  const first = [...book.value.reports].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  )[0];
  return first ? first.created_at.slice(0, 10) : '—';
});

const shouldWarn = computed(() => {
  if (!book.value?.reports?.length) return false;
  const up = book.value.reports.reduce((s, r) => s + r.upvote, 0);
  const down = book.value.reports.reduce((s, r) => s + r.downvote, 0);
  return up - down >= 5 && up >= 3;
});

onMounted(() => load(route.params.isbn as string));
watch(
  () => route.params.isbn,
  (isbn) => load(isbn as string),
);
</script>

<style scoped>
.book-detail {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 48px;
  align-items: start;
}
.book-detail__meta { position: sticky; top: 24px; }
.state-loading,
.state-empty {
  text-align: center;
  padding: 64px 32px;
  font-family: var(--font-cn);
  color: var(--ink-faint);
  letter-spacing: 0.04em;
}
.state-empty { font-style: italic; color: var(--ink-soft); }
.state-error {
  text-align: center;
  padding: 64px 32px;
  color: var(--quarantine-warn);
  font-family: var(--font-cn);
}
.book-detail__title {
  font-family: var(--font-cn-display);
  font-weight: 700;
  font-size: clamp(28px, 3.6vw, 38px);
  line-height: 1.18;
  letter-spacing: 0.01em;
  margin-top: 18px;
  color: var(--ink);
}
.book-detail__author {
  font-family: var(--font-cn);
  font-size: 16px;
  color: var(--ink-soft);
  margin: 6px 0;
}
.book-detail__meta-line {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  margin-bottom: 14px;
}
@media (max-width: 900px) {
  .book-detail { grid-template-columns: 1fr; }
  .book-detail__meta { position: static; }
}
</style>