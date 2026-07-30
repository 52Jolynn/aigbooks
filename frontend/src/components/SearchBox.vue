<template>
  <div class="search-box">
    <span class="search-box__label">LIBRARY CARD</span>
    <input
      v-model="localQ"
      type="search"
      class="search-box__input"
      :placeholder="placeholder"
      @keyup.enter="onSearch"
      @input="onDebouncedSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';

const props = withDefaults(
  defineProps<{ modelValue?: string; placeholder?: string; debounce?: number }>(),
  { modelValue: '', placeholder: 'Search by title, author, ISBN or description', debounce: 300 },
);
const emit = defineEmits<{ 'update:modelValue': [string]; search: [string] }>();

const router = useRouter();
const localQ = ref(props.modelValue);

let timer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.modelValue,
  (v) => (localQ.value = v),
);

function onDebouncedSearch() {
  emit('update:modelValue', localQ.value);
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => emit('search', localQ.value), props.debounce);
}

function onSearch() {
  if (timer) clearTimeout(timer);
  router.push({ name: 'search', query: { q: localQ.value } });
}
</script>

<style scoped>
.search-box {
  display: inline-block;
  border: 1px solid var(--rule);
  padding: 12px 18px;
  background: var(--paper);
  font-family: var(--font-mono);
}
.search-box__label {
  display: block;
  font-size: 10px;
  letter-spacing: 0.18em;
  color: var(--stamp-red);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.search-box__input {
  border: none;
  background: transparent;
  font-family: var(--font-mono);
  font-size: 16px;
  color: var(--ink);
  width: 320px;
  outline: none;
}
</style>
