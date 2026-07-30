<template>
  <article class="report">
    <div class="report__category">{{ category }}</div>
    <h4 class="report__title">
      <RouterLink :to="`/books/${report.book.isbn}`">{{ report.book.title }}</RouterLink>
    </h4>
    <p class="report__author">{{ report.book.author }}</p>
    <p class="report__isbn">ISBN {{ report.book.isbn }}</p>
    <p class="report__excerpt">{{ excerpt }}</p>
    <div class="report__footer">
      <span>filed {{ filedDate }}</span>
      <Stamp :count="report.book.report_count" size="mini" />
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ReportOut } from '@/api/books';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut; index?: number }>();

const excerpt = computed(() => {
  const text = props.report.description;
  return text.length > 120 ? text.slice(0, 117) + '...' : text;
});

const category = computed(() => {
  const diff = Date.now() - new Date(props.report.created_at).getTime();
  const days = Math.floor(diff / 86400000);
  if (days < 1) return 'Filed Today';
  if (days === 1) return 'Filed Yesterday';
  return `Filed ${days} days ago`;
});

const filedDate = computed(() => props.report.created_at.slice(0, 10));
</script>
