<template>
  <main class="ledger">
    <div v-if="loading" style="text-align:center; padding:64px 32px">Loading...</div>
    <div
      v-else-if="error"
      style="text-align:center; padding:64px 32px; color:var(--stamp-red)"
    >
      {{ error }}
    </div>
    <div v-else-if="book" class="book-detail">
      <div class="book-detail__meta">
        <div class="book-detail__cover">
          <img
            v-if="book.cover_path"
            :src="`/covers/${book.cover_path}`"
            :alt="book.title"
          />
          <span v-else>A.</span>
        </div>
        <h1 class="book-detail__title">{{ book.title }}</h1>
        <p class="book-detail__author">{{ book.author }}</p>
        <p class="book-detail__isbn">ISBN {{ book.isbn }}</p>
        <Stamp :count="book.report_count" size="featured">
          Reported × {{ book.report_count }}
        </Stamp>
      </div>
      <div class="book-detail__reports">
        <SectionHeader
          num="§ 03 —"
          title="Filings"
          :meta="`${book.reports.length} report${book.reports.length > 1 ? 's' : ''}`"
        />
        <article v-for="r in book.reports" :key="r.id" class="book-detail__report">
          <p class="book-detail__report-desc">"{{ r.description }}"</p>
          <EvidenceList :evidences="r.evidences" />
          <div class="book-detail__report-footer">
            <span>filed {{ r.created_at.slice(0, 10) }}</span>
            <VoteButton :report="r" />
          </div>
        </article>
        <div
          v-if="!book.reports.length"
          style="text-align:center; padding:32px; font-style:italic; color:var(--ink-soft)"
        >
          No reports for this ISBN.
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { getBookDetail, type BookDetailOut } from '@/api/books';
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
    error.value =
      status === 404 ? 'No dossier entry found for this ISBN.' : 'Failed to load.';
  } finally {
    loading.value = false;
  }
}

onMounted(() => load(route.params.isbn as string));
watch(
  () => route.params.isbn,
  (isbn) => load(isbn as string),
);
</script>

<style scoped>
.book-detail {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 48px;
}
.book-detail__cover {
  width: 100%;
  aspect-ratio: 3/4;
  background: var(--paper-dark);
  border: 1px solid var(--rule);
  display: grid;
  place-items: center;
  font-family: var(--font-display);
  font-style: italic;
  font-size: 64px;
  color: var(--ink-faint);
}
.book-detail__cover img { width: 100%; height: 100%; object-fit: cover; }
.book-detail__title {
  font-family: var(--font-display);
  font-variation-settings: "opsz" 60, "wght" 700;
  font-size: 44px;
  line-height: 1.05;
  margin-top: 24px;
  letter-spacing: -0.02em;
}
.book-detail__author {
  font-family: var(--font-body);
  font-style: italic;
  font-size: 22px;
  color: var(--ink-soft);
  margin: 6px 0;
}
.book-detail__isbn {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-faint);
  margin-bottom: 16px;
}
.book-detail__report {
  border-top: 1px solid var(--rule);
  padding: 20px 0;
}
.book-detail__report-desc {
  font-family: var(--font-body);
  font-style: italic;
  font-size: 17px;
  color: var(--ink-soft);
  border-left: 3px solid var(--stamp-red);
  padding-left: 16px;
  margin-bottom: 12px;
}
.book-detail__report-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faint);
  border-top: 1px dashed var(--paper-shadow);
  padding-top: 10px;
}
@media (max-width: 900px) {
  .book-detail { grid-template-columns: 1fr; }
}
</style>
