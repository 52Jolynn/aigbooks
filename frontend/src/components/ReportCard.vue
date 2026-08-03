<template>
  <article class="sample-bag">
    <RouterLink :to="detailLink" class="sample-bag__cover-link" :aria-label="coverLinkAria">
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
    </RouterLink>
    <h3 class="sample-bag__title">
      <RouterLink :to="detailLink">{{ report.identifier.title }}</RouterLink>
    </h3>
    <p class="sample-bag__author">{{ report.identifier.author }}</p>
    <p class="sample-bag__excerpt">{{ excerpt }}</p>
    <dl class="sample-bag__meta">
      <dt>{{ card.field.type }}</dt>
      <dd>{{ typeLabel }}</dd>
      <dt>{{ card.field.identifier }}</dt>
      <dd class="sample-bag__meta-id">{{ report.identifier.identifier }}</dd>
      <dt>{{ card.filedOn }}</dt>
      <dd>{{ filedDate }}</dd>
      <dt>{{ card.reportedCount(report.identifier.report_count) }}</dt>
      <dd>{{ report.upvote + report.downvote }} 票 · {{ report.evidences.length }} 份证据</dd>
    </dl>
    <div class="sample-bag__footer">
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
import { card } from '@/i18n/zh';
import DefaultCover from './DefaultCover.vue';
import Stamp from './Stamp.vue';

const props = defineProps<{ report: ReportOut; index?: number }>();

const defaultCoverAlt = computed(
  () => `${props.report.identifier.title} · 默认封面 / ${card.noCover}`,
);

const coverLinkAria = computed(
  () => `查看 ${props.report.identifier.title} 的详情`,
);

const typeLabel = computed(() => IDENTIFIER_TYPE_LABEL[props.report.identifier.type]);

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
</script>