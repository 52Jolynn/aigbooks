<template>
  <header class="masthead" role="banner">
    <div class="masthead__top">
      <span class="masthead__case" :aria-label="`${masthead.caseLabel} ${caseNumber}`">
        {{ masthead.caseLabel }} · {{ caseNumber }}
      </span>
      <div class="masthead__center">
        <span class="masthead__tagline">{{ masthead.tagline }}</span>
        <span class="masthead__date">{{ today }}</span>
      </div>
      <div class="masthead__actions">
        <a
          href="/api/feed/reports.rss"
          class="masthead__rss"
          target="_blank"
          rel="noopener noreferrer"
        >{{ nav.rss }}</a>
        <RouterLink to="/report" class="masthead__cta">{{ nav.submit }}</RouterLink>
      </div>
    </div>
    <div class="masthead__title">
      <h1 class="masthead__title-zh">{{ site.brand }}</h1>
      <span class="masthead__title-en" aria-hidden="true">{{ site.brandEn }}</span>
    </div>
    <p class="masthead__sub">{{ masthead.tagline }}</p>
    <nav class="masthead__nav" :aria-label="nav.primary">
      <RouterLink to="/" :class="{ 'is-active': route.name === 'home' }">{{ nav.latest }}</RouterLink>
      <RouterLink to="/search" :class="{ 'is-active': route.name === 'search' }">{{ nav.search }}</RouterLink>
      <RouterLink to="/report" :class="{ 'is-active': route.name === 'report' }">{{ nav.submit }}</RouterLink>
      <a href="/api/feed/reports.rss" target="_blank" rel="noopener noreferrer">{{ nav.rss }}</a>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useRecentStore } from '@/stores/reports';
import { formatCaseNumber, formatLongDate, masthead, nav, site } from '@/i18n/zh';

const route = useRoute();
const store = useRecentStore();
const reportCount = computed(() => store.total ?? '—');

const caseNumber = computed(() => formatCaseNumber(reportCount.value, new Date()));
const today = formatLongDate(new Date());
</script>