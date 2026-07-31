<template>
  <div class="search-box">
    <label class="search-box__label" :for="inputId">{{ cardLabel }}</label>
    <input
      :id="inputId"
      ref="inputEl"
      v-model="localQ"
      type="search"
      class="search-box__input"
      :placeholder="placeholder"
      :aria-label="ariaLabel"
      @keyup.enter="onSearch"
      @input="onDebouncedSearch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { search as searchI18n, searchBox as i18n } from '@/i18n/zh';

const props = withDefaults(
  defineProps<{ modelValue?: string; placeholder?: string; debounce?: number }>(),
  { modelValue: '', placeholder: searchI18n.placeholder, debounce: 300 },
);
const emit = defineEmits<{ 'update:modelValue': [string]; search: [string] }>();

const router = useRouter();
const localQ = ref(props.modelValue);
const inputEl = ref<HTMLInputElement | null>(null);

const inputId = `search-box-${Math.random().toString(36).slice(2, 8)}`;
const cardLabel = i18n.cardLabel;
const ariaLabel = i18n.ariaLabel;

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

defineExpose({ inputEl });
</script>