import { defineStore } from 'pinia';
import { ref } from 'vue';
import { getRecentReports, type ReportOut } from '@/api/books';

export const useRecentStore = defineStore('recent', () => {
  const reports = ref<ReportOut[]>([]);
  const total = ref<number | null>(null);
  const loading = ref(false);

  async function refresh() {
    loading.value = true;
    try {
      const data = await getRecentReports();
      reports.value = data.reports;
      total.value = data.total;
    } catch (e) {
      console.warn('Failed to load recent reports:', e);
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  return { reports, total, loading, refresh };
});
