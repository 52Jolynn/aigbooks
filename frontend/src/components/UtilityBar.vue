<template>
  <nav class="utility" :aria-label="nav.shortcuts">
    <a
      href="/api/feed/reports.rss"
      class="utility__rss"
      target="_blank"
      rel="noopener noreferrer"
    >{{ utility.rssLabel }}</a>
    <RouterLink class="utility__btn" to="/report">{{ utility.submitLabel }}</RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { nav, utility } from '@/i18n/zh';
</script>