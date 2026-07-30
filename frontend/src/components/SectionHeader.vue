<template>
  <div class="section-head">
    <span class="section-head__num">{{ num }}</span>
    <h2 class="section-head__title">{{ title }}</h2>
    <span class="section-head__meta">{{ meta }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{ num: string; title: string; meta?: string }>();
</script>
