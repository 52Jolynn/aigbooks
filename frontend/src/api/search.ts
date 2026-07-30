import api from './index';
import type { ReportOut } from './books';

export interface SearchResultOut {
  reports: ReportOut[];
  total: number;
  query: string;
}

export const searchReports = (q: string) =>
  api.get<SearchResultOut>('/search', { params: { q } }).then((r) => r.data);
