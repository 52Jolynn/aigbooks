<template>
  <div class="form-field" :class="{ 'form-field--invalid': !!error }">
    <label class="form-field__label" :for="fieldId">{{ label }}</label>
    <input
      v-if="!multiline"
      :id="fieldId"
      :value="modelValue"
      :type="type ?? 'text'"
      :placeholder="placeholder ?? ''"
      :aria-invalid="!!error"
      :aria-describedby="error ? errorId : undefined"
      class="form-field__input"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <textarea
      v-else
      :id="fieldId"
      :value="modelValue"
      :placeholder="placeholder ?? ''"
      :aria-invalid="!!error"
      :aria-describedby="error ? errorId : undefined"
      class="form-field__input form-field__textarea"
      @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
    <p v-if="error" :id="errorId" class="form-field__error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  label: string;
  modelValue: string;
  type?: string;
  placeholder?: string;
  multiline?: boolean;
  error?: string;
}>();
void props;
const emit = defineEmits<{ 'update:modelValue': [string] }>();

const suffix = Math.random().toString(36).slice(2, 8);
const fieldId = `form-field-${suffix}`;
const errorId = `form-field-${suffix}-error`;
</script>