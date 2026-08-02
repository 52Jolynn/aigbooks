<template>
  <main class="ledger">
    <div v-if="loading" class="state-loading">{{ detail.loading }}</div>
    <div v-else-if="error" class="state-error">{{ error }}</div>
    <div v-else-if="identifier" class="identifier-detail">
      <aside class="identifier-detail__meta">
        <div class="sample-bag">
          <div class="sample-bag__cover">
            <img
              v-if="coverSrc && !coverFailed"
              :src="coverSrc"
              :alt="identifier.title"
              @error="coverFailed = true"
            />
            <DefaultCover
              v-else
              :aria-label="defaultCoverAlt"
              :type="identifier.type"
              :identifier="identifier.identifier"
              :title="identifier.title"
              :author="identifier.author"
              :report-count="identifier.report_count"
              :created-at="identifier.created_at"
            />
          </div>
        </div>
        <h1 class="identifier-detail__title">{{ identifier.title }}</h1>
        <p class="identifier-detail__author">{{ identifier.author }}</p>
        <p class="identifier-detail__meta-line">
          {{ typeLabel }} {{ identifier.identifier }}
        </p>
        <Stamp :count="identifier.report_count" size="featured">
          {{ card.reportedCount(identifier.report_count) }}
        </Stamp>

        <div class="sample-bag__corners">
          <span class="sample-bag__corner">
            {{ typeLabel }} {{ identifier.identifier }}
          </span>
          <span class="sample-bag__corner">{{ earliestLabel }}</span>
        </div>

        <div v-if="shouldWarn" class="identifier-detail__warning" role="note">
          <p class="identifier-detail__warning-title">{{ detail.warningTitle }}</p>
          <p>{{ detail.warningBody }}</p>
        </div>
      </aside>

      <section class="identifier-detail__reports">
        <SectionHeader
          :num="detail.sectionNum"
          :title="detail.sectionTitle"
          :meta="detail.sectionMeta(identifier.reports.length)"
        />
        <ul v-if="identifier.reports.length" class="report-timeline">
          <li v-for="r in identifier.reports" :key="r.id" class="report-timeline__item">
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
              <VoteButton :report="r" @voted="onReportVoted(r.id, $event)" />
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
import {
  getIdentifierDetail,
  IDENTIFIER_TYPE_LABEL,
  type IdentifierDetailOut,
  type IdentifierType,
  type ReportOut,
} from '@/api/identifiers';
import { card, detail, formatCaseNumber } from '@/i18n/zh';
import DefaultCover from '@/components/DefaultCover.vue';
import SectionHeader from '@/components/SectionHeader.vue';
import Stamp from '@/components/Stamp.vue';
import VoteButton from '@/components/VoteButton.vue';
import EvidenceList from '@/components/EvidenceList.vue';

const route = useRoute();
const identifier = ref<IdentifierDetailOut | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const typeLabel = computed(() => {
  const t = (route.params.type as IdentifierType) ?? 'isbn';
  return IDENTIFIER_TYPE_LABEL[t] ?? t.toUpperCase();
});

const defaultCoverAlt = computed(() =>
  identifier.value ? `${identifier.value.title} · 默认封面` : '默认封面',
);

const coverSrc = computed(() =>
  identifier.value?.cover_path ? `/covers/${identifier.value.cover_path}` : null,
);

const coverFailed = ref(false);
watch(
  () => identifier.value?.cover_path,
  () => {
    coverFailed.value = false;
  },
);

async function load(type: IdentifierType, id: string) {
  loading.value = true;
  error.value = null;
  try {
    identifier.value = await getIdentifierDetail(type, id);
  } catch (e: unknown) {
    identifier.value = null;
    const status = (e as { response?: { status?: number } })?.response?.status;
    error.value = status === 404 ? detail.notFound : detail.loadFailed;
  } finally {
    loading.value = false;
  }
}

const earliestLabel = computed(() => {
  if (!identifier.value?.reports?.length) return '—';
  const first = [...identifier.value.reports].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  )[0];
  return first ? first.created_at.slice(0, 10) : '—';
});

const shouldWarn = computed(() => {
  if (!identifier.value?.reports?.length) return false;
  const up = identifier.value.reports.reduce((s, r) => s + r.upvote, 0);
  const down = identifier.value.reports.reduce((s, r) => s + r.downvote, 0);
  return up - down >= 5 && up >= 3;
});

function onReportVoted(id: number, updated: ReportOut) {
  if (!identifier.value) return;
  const idx = identifier.value.reports.findIndex(r => r.id === id);
  if (idx < 0) return;
  identifier.value.reports[idx] = { ...identifier.value.reports[idx], ...updated };
}

onMounted(() => load(route.params.type as IdentifierType, route.params.identifier as string));
watch(
  () => [route.params.type, route.params.identifier],
  ([type, id]) => load(type as IdentifierType, id as string),
);
</script>

<style scoped>
.identifier-detail {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 48px;
  align-items: start;
}
.identifier-detail__meta { position: sticky; top: 24px; }
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
.identifier-detail__title {
  font-family: var(--font-cn-display);
  font-weight: 700;
  font-size: clamp(28px, 3.6vw, 38px);
  line-height: 1.18;
  letter-spacing: 0.01em;
  margin-top: 18px;
  color: var(--ink);
}
.identifier-detail__author {
  font-family: var(--font-cn);
  font-size: 16px;
  color: var(--ink-soft);
  margin: 6px 0;
}
.identifier-detail__meta-line {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  margin-bottom: 14px;
}
@media (max-width: 900px) {
  .identifier-detail { grid-template-columns: 1fr; }
  .identifier-detail__meta { position: static; }
}
</style>