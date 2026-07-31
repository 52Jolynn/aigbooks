<template>
  <article class="sample-bag">
    <div class="sample-bag__cover">
      <img
        v-if="report.book.cover_path"
        :src="coverUrl ?? ''"
        :alt="report.book.title"
      />
      <span v-else class="sample-bag__cover-fallback">{{ card.noCover }}</span>
      <span class="sample-bag__cover-corner sample-bag__cover-corner--bl">
        ISBN {{ report.book.isbn }}
      </span>
      <span class="sample-bag__cover-corner sample-bag__cover-corner--br">
        {{ caseNumber }}
      </span>
    </div>
    <h3 class="sample-bag__title">
      <RouterLink :to="`/books/${report.book.isbn}`">{{ report.book.title }}</RouterLink>
    </h3>
    <p class="sample-bag__author">{{ report.book.author }}</p>
    <p class="sample-bag__excerpt">{{ excerpt }}</p>
    <dl class="sample-bag__meta">
      <dt>{{ card.filedOn }}</dt>
      <dd>{{ filedDate }}</dd>
      <dt>{{ card.reportedCount(report.book.report_count) }}</dt>
      <dd>{{ report.upvote + report.downvote }} 票 · {{ report.evidences.length }} 份证据</dd>
    </dl>
    <div class="sample-bag__footer">
      <span class="quarantine-stamp" :class="statusClass">{{ statusLabel }}</span>
      <Stamp :count="report.book.report_count" size="mini" />
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ReportOut } from '@/api/books';
import { card, formatCaseNumber } from '@/i18n/zh';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut; index?: number }>();

const coverUrl = computed(() =>
  props.report.book.cover_path ? `/covers/${props.report.book.cover_path}` : null,
);

const excerpt = computed(() => {
  const text = props.report.description;
  return text.length > 120 ? text.slice(0, 117) + '...' : text;
});

const filedDate = computed(() => props.report.created_at.slice(0, 10));
const caseNumber = computed(() => formatCaseNumber(props.report.id, new Date(props.report.created_at)));

const statusLabel = computed(() => card.filedOn);
const statusClass = computed(() => 'quarantine-stamp--ok');
</script>