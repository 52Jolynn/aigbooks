import { defineStore } from 'pinia';
import { ref } from 'vue';
import { generateFingerprint } from '@/utils/fingerprint';

export const useFingerprintStore = defineStore('fingerprint', () => {
  const fp = ref<string | null>(null);

  async function ensure() {
    if (!fp.value) {
      fp.value = await generateFingerprint();
    }
    return fp.value;
  }

  return { fp, ensure };
});
