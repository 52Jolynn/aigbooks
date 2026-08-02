import api from './index';
import type { IdentifierType } from './identifiers';

export interface CreateReportInput {
  type: IdentifierType;
  identifier: string;
  title: string;
  author: string;
  description: string;
  fingerprint: string;
  cover?: File;
  evidences?: File[];
}

export const createReport = (input: CreateReportInput) => {
  const form = new FormData();
  form.append('type', input.type);
  form.append('identifier', input.identifier);
  form.append('title', input.title);
  form.append('author', input.author);
  form.append('description', input.description);
  form.append('fingerprint', input.fingerprint);
  if (input.cover) form.append('cover', input.cover);
  input.evidences?.forEach((file) => form.append('evidences', file));
  return api.post('/reports', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const voteReport = (id: number, voteType: -1 | 1, fingerprint: string) =>
  api.post(`/reports/${id}/vote`, { vote_type: voteType, fingerprint });