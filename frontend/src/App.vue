<template>
  <Masthead />
  <RouterView />
  <UtilityBar />
  <Colophon />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRecentStore } from '@/stores/reports';
import Masthead from '@/components/Masthead.vue';
import UtilityBar from '@/components/UtilityBar.vue';
import Colophon from '@/components/Colophon.vue';

const store = useRecentStore();
onMounted(() => store.refresh());
</script>
