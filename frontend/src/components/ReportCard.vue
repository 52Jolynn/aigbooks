<template>
  <article class="sample-bag">
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
    <h3 class="sample-bag__title">
      <RouterLink :to="detailLink">{{ report.identifier.title }}</RouterLink>
    </h3>
    <p class="sample-bag__author">{{ report.identifier.author }}</p>
    <p class="sample-bag__excerpt">{{ excerpt }}</p>
    <div class="sample-bag__corners">
      <span class="sample-bag__corner">
        {{ typeLabel }} {{ report.identifier.identifier }}
      </span>
      <span class="sample-bag__corner">{{ caseNumber }}</span>
    </div>
    <dl class="sample-bag__meta">
      <dt>{{ card.filedOn }}</dt>
      <dd>{{ filedDate }}</dd>
      <dt>{{ card.reportedCount(report.identifier.report_count) }}</dt>
      <dd>{{ report.upvote + report.downvote }} 票 · {{ report.evidences.length }} 份证据</dd>
    </dl>
    <div class="sample-bag__footer">
      <span class="quarantine-stamp" :class="statusClass">{{ statusLabel }}</span>
      <Stamp :count="report.identifier.report_count" size="mini" />
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import {
  IDENTIFIER_TYPE_LABEL,
  type ReportOut,
} from '@/api/identifiers';
import { card, formatCaseNumber } from '@/i18n/zh';
import DefaultCover from './DefaultCover.vue';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut; index?: number }>();

const typeLabel = computed(() => IDENTIFIER_TYPE_LABEL[props.report.identifier.type]);

const defaultCoverAlt = computed(
  () => `${props.report.identifier.title} · 默认封面 / ${card.noCover}`,
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

const excerpt = computed(() => {
  const text = props.report.description;
  return text.length > 120 ? text.slice(0, 117) + '...' : text;
});

const filedDate = computed(() => props.report.created_at.slice(0, 10));
const caseNumber = computed(() => formatCaseNumber(props.report.id, new Date(props.report.created_at)));

const statusLabel = computed(() => card.filedOn);
const statusClass = computed(() => 'quarantine-stamp--ok');
</script>