<template>
  <header class="masthead">
    <div class="masthead__top">
      <span>Vol. III · No. {{ reportCount }}</span>
      <span>An Anonymous Reader's Dossier</span>
      <span>{{ today }}</span>
    </div>
    <h1 class="masthead__title">AIG<em>books</em></h1>
    <p class="masthead__sub">a registry of machine-printed trash you shouldn't pay for</p>
    <nav class="masthead__nav">
      <RouterLink to="/" :class="{ 'is-active': route.name === 'home' }">Latest</RouterLink>
      <RouterLink to="/search" :class="{ 'is-active': route.name === 'search' }">Search</RouterLink>
      <RouterLink to="/report" :class="{ 'is-active': route.name === 'report' }">Submit Report</RouterLink>
      <a href="/api/feed/reports.rss" target="_blank" rel="noopener">RSS</a>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useRecentStore } from '@/stores/reports';

const route = useRoute();
const store = useRecentStore();
const reportCount = computed(() => store.total ?? '—');

const today = new Date().toLocaleDateString('en-US', {
  weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
});
</script>
