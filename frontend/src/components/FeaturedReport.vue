<template>
  <article class="featured">
    <div class="featured__cover">
      <div class="sample-bag">
        <div class="sample-bag__cover">
          <img
            v-if="coverSrc && !coverFailed"
            :src="coverSrc"
            :alt="report.identifier.title"
            @error="coverFailed = true"
          />
          <DefaultCover
            v-else
            :aria-label="defaultCoverAlt"
            :type="report.identifier.type"
            :identifier="report.identifier.identifier"
            :title="report.identifier.title"
            :author="report.identifier.author"
            :report-count="report.identifier.report_count"
          />
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
import { computed, ref, watch } from 'vue';
import {
  IDENTIFIER_TYPE_LABEL,
  type ReportOut,
} from '@/api/identifiers';
import { card, formatRelative } from '@/i18n/zh';
import DefaultCover from './DefaultCover.vue';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut }>();

const typeLabel = computed(() => IDENTIFIER_TYPE_LABEL[props.report.identifier.type]);

const defaultCoverAlt = computed(
  () => `${props.report.identifier.title} · 默认封面 / 无封面`,
);

const coverSrc = computed(() =>
  props.report.identifier.cover_path
    ? `/covers/${props.report.identifier.cover_path}`
    : null,
);

const coverFailed = ref(false);
watch(
  () => props.report.identifier.cover_path,
  () => {
    coverFailed.value = false;
  },
);

const detailLink = computed(
  () =>
    `/identifiers/${props.report.identifier.type}/${encodeURIComponent(props.report.identifier.identifier)}`,
);

const relativeTime = computed(() => formatRelative(props.report.created_at));
</script>