<template>
  <article class="featured">
    <div class="featured__cover">
      <div class="sample-bag">
        <div class="sample-bag__cover">
          <img
            v-if="report.identifier.cover_path"
            :src="coverUrl ?? ''"
            :alt="report.identifier.title"
          />
          <span v-else class="sample-bag__cover-fallback">无</span>
          <span class="sample-bag__cover-corner sample-bag__cover-corner--bl">
            {{ typeLabel }} {{ report.identifier.identifier }}
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
        <RouterLink :to="detailLink">{{ report.identifier.title }}</RouterLink>
      </h2>
      <p class="featured__author">{{ report.identifier.author }}</p>
      <p class="featured__meta">
        {{ typeLabel }} {{ report.identifier.identifier }} ·
        {{ card.reportedCount(report.identifier.report_count) }}
      </p>
      <blockquote class="featured__lede">「{{ report.description }}」</blockquote>
      <Stamp :count="report.identifier.report_count" size="featured">
        {{ card.reportedCount(report.identifier.report_count) }}
      </Stamp>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  IDENTIFIER_TYPE_LABEL,
  type ReportOut,
} from '@/api/identifiers';
import { card, formatCaseNumber, formatRelative } from '@/i18n/zh';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut }>();

const typeLabel = computed(() => IDENTIFIER_TYPE_LABEL[props.report.identifier.type]);

const coverUrl = computed(() =>
  props.report.identifier.cover_path
    ? `/covers/${props.report.identifier.cover_path}`
    : null,
);

const detailLink = computed(
  () =>
    `/identifiers/${props.report.identifier.type}/${encodeURIComponent(props.report.identifier.identifier)}`,
);

const relativeTime = computed(() => formatRelative(props.report.created_at));
const caseNumber = computed(() => formatCaseNumber(props.report.id, new Date(props.report.created_at)));
</script>