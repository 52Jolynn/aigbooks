<template>
  <article class="featured">
    <div class="featured__cover">
      <img v-if="report.book.cover_path" :src="coverUrl ?? ''" :alt="report.book.title" />
      <span v-else>A.</span>
    </div>
    <div>
      <div class="featured__category">Reported {{ relativeTime }}</div>
      <h3 class="featured__title">
        <RouterLink :to="`/books/${report.book.isbn}`">{{ report.book.title }}</RouterLink>
      </h3>
      <p class="featured__author">{{ report.book.author }}</p>
      <p class="featured__isbn">ISBN {{ report.book.isbn }}</p>
      <blockquote class="featured__lede">"{{ report.description }}"</blockquote>
      <Stamp :count="report.book.report_count" size="featured">
        Reported × {{ report.book.report_count }}
      </Stamp>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ReportOut } from '@/api/books';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut }>();

const coverUrl = computed(() =>
  props.report.book.cover_path ? `/covers/${props.report.book.cover_path}` : null,
);

const relativeTime = computed(() => {
  const diff = Date.now() - new Date(props.report.created_at).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return 'just now';
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? 's' : ''} ago`;
});
</script>
