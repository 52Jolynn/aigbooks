<template>
  <a class="skip-link" href="#main">{{ a11y.skipLink }}</a>
  <div class="app-shell">
    <Masthead />
    <main id="main" class="main" tabindex="-1">
      <RouterView />
    </main>
    <UtilityBar />
    <Colophon />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRecentStore } from '@/stores/reports';
import { a11y } from '@/i18n/zh';
import Masthead from '@/components/Masthead.vue';
import UtilityBar from '@/components/UtilityBar.vue';
import Colophon from '@/components/Colophon.vue';

const store = useRecentStore();
onMounted(() => store.refresh());
</script>