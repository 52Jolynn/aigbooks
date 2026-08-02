import api from './index';

export type IdentifierType = 'isbn' | 'issn' | 'issn-l';

export const IDENTIFIER_TYPE_LABEL: Record<IdentifierType, string> = {
  isbn: 'ISBN',
  issn: 'ISSN',
  'issn-l': 'ISSN-L',
};

export const IDENTIFIER_TYPE_PLACEHOLDER: Record<IdentifierType, string> = {
  isbn: '978-7-100-12345-6',
  issn: '1003-7055',
  'issn-l': '1003-7055',
};

export interface IdentifierSummary {
  type: IdentifierType;
  identifier: string;
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
  identifier: IdentifierSummary;
  description: string;
  upvote: number;
  downvote: number;
  created_at: string;
  evidences: EvidenceOut[];
}

export interface IdentifierDetailOut extends IdentifierSummary {
  created_at: string;
  updated_at: string;
  reports: ReportOut[];
}

export interface RecentReportsOut {
  reports: ReportOut[];
  total: number;
}

export const getRecentIdentifiers = () =>
  api.get<RecentReportsOut>('/identifiers/recent').then((r) => r.data);

export const getIdentifierDetail = (type: IdentifierType, identifier: string) =>
  api
    .get<IdentifierDetailOut>(`/identifiers/${type}/${encodeURIComponent(identifier)}`)
    .then((r) => r.data);