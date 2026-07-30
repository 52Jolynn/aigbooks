<template>
  <div class="form-field">
    <label class="form-field__label">{{ label }}</label>
    <input
      v-if="!multiline"
      :value="modelValue"
      :type="type ?? 'text'"
      :placeholder="placeholder ?? ''"
      class="form-field__input"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <textarea
      v-else
      :value="modelValue"
      :placeholder="placeholder ?? ''"
      class="form-field__input form-field__textarea"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
    <p v-if="error" class="form-field__error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  modelValue: string;
  type?: string;
  placeholder?: string;
  multiline?: boolean;
  error?: string;
}>();
const emit = defineEmits<{ 'update:modelValue': [string] }>();
</script>

<style scoped>
.form-field { margin-bottom: 18px; }
.form-field__label {
  display: block;
  font-family: var(--font-display);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-soft);
  margin-bottom: 4px;
}
.form-field__input {
  width: 100%;
  border: none;
  border-bottom: 1px solid var(--rule);
  background: transparent;
  padding: 8px 0;
  font-family: var(--font-body);
  font-size: 18px;
  color: var(--ink);
  outline: none;
  border-radius: 0;
}
.form-field__textarea { min-height: 100px; resize: vertical; }
.form-field__error {
  color: var(--stamp-red);
  font-size: 12px;
  margin-top: 4px;
  font-family: var(--font-mono);
}
</style>
