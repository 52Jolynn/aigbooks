import api from './index';

export interface BookSummary {
  isbn: string;
  title: string;
  author: string;
  cover_path: string | null;
  report_count: number;
}

export interface EvidenceOut {
  id: number;
  file_path: string;
  file_kind: string;
  mime_type: string | null;
  size_bytes: number | null;
  created_at: string;
}

export interface ReportOut {
  id: number;
  book: BookSummary;
  description: string;
  upvote: number;
  downvote: number;
  created_at: string;
  evidences: EvidenceOut[];
}

export interface BookDetailOut extends BookSummary {
  created_at: string;
  updated_at: string;
  reports: ReportOut[];
}

export interface RecentReportsOut {
  reports: ReportOut[];
  total: number;
}

export const getRecentReports = () =>
  api.get<RecentReportsOut>('/books/recent').then((r) => r.data);

export const getBookDetail = (isbn: string) =>
  api.get<BookDetailOut>(`/books/${isbn}`).then((r) => r.data);
