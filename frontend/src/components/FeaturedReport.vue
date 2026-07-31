<template>
  <article class="featured">
    <div class="featured__cover">
      <div class="sample-bag">
        <div class="sample-bag__cover">
          <img
            v-if="report.book.cover_path"
            :src="coverUrl ?? ''"
            :alt="report.book.title"
          />
          <span v-else class="sample-bag__cover-fallback">无</span>
          <span class="sample-bag__cover-corner sample-bag__cover-corner--bl">
            ISBN {{ report.book.isbn }}
          </span>
          <span class="sample-bag__cover-corner sample-bag__cover-corner--br">
            {{ caseNumber }}
          </span>
        </div>
      </div>
    </div>

    <div>
      <div class="featured__meta">
        <span class="quarantine-stamp quarantine-stamp--ok">
          {{ card.filedOn }} {{ relativeTime }}
        </span>
      </div>
      <h2 class="featured__title">
        <RouterLink :to="`/books/${report.book.isbn}`">{{ report.book.title }}</RouterLink>
      </h2>
      <p class="featured__author">{{ report.book.author }}</p>
      <p class="featured__meta">
        ISBN {{ report.book.isbn }} · {{ card.reportedCount(report.book.report_count) }}
      </p>
      <blockquote class="featured__lede">「{{ report.description }}」</blockquote>
      <Stamp :count="report.book.report_count" size="featured">
        {{ card.reportedCount(report.book.report_count) }}
      </Stamp>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ReportOut } from '@/api/books';
import { card, formatCaseNumber, formatRelative } from '@/i18n/zh';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut }>();

const coverUrl = computed(() =>
  props.report.book.cover_path ? `/covers/${props.report.book.cover_path}` : null,
);

const relativeTime = computed(() => formatRelative(props.report.created_at));
const caseNumber = computed(() => formatCaseNumber(props.report.id, new Date(props.report.created_at)));
</script>