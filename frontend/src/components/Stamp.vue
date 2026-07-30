<template>
  <span :class="['stamp', `stamp--${size}`]" ref="rootEl">
    <slot>{{ count !== null ? `× ${count}` : '' }}</slot>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = withDefaults(
  defineProps<{ count?: number | null; size?: 'featured' | 'mini' }>(),
  { size: 'mini', count: null },
);
void props;

const rootEl = ref<HTMLElement | null>(null);

defineExpose({
  pulse() {
    if (!rootEl.value) return;
    rootEl.value.classList.remove('stamp--pulse');
    void rootEl.value.offsetWidth;
    rootEl.value.classList.add('stamp--pulse');
  },
});
</script>
