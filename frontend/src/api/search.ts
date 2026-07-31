import api from './index';
import type { ReportOut } from './books';

export type SearchField = 'all' | 'isbn' | 'title' | 'author' | 'description';

export interface SearchResultOut {
  reports: ReportOut[];
  total: number;
  query: string;
}

export const searchReports = (q: string, field: SearchField = 'all') =>
  api
    .get<SearchResultOut>('/search', { params: { q, field: field === 'all' ? undefined : field } })
    .then((r) => r.data);
