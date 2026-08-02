import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getRecentIdentifiers, type ReportOut } from '@/api/identifiers';
import { consoleMessages } from '@/i18n/zh';

export const useRecentStore = defineStore('recent', () => {
  const reports = ref<ReportOut[]>([]);
  const total = ref<number | null>(null);
  const loading = ref(false);

  async function refresh() {
    loading.value = true;
    try {
      const data = await getRecentIdentifiers();
      reports.value = data.reports;
      total.value = data.total;
    } catch (e) {
      console.warn(consoleMessages.recentFailed, e);
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  return { reports, total, loading, refresh };
});