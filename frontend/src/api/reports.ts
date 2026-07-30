import api from './index';

export interface CreateReportInput {
  isbn: string;
  title: string;
  author: string;
  description: string;
  fingerprint: string;
  cover?: File;
  evidences?: File[];
}

export const createReport = (input: CreateReportInput) => {
  const form = new FormData();
  form.append('isbn', input.isbn);
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
