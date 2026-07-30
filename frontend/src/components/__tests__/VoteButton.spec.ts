import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import VoteButton from '../VoteButton.vue';
import type { ReportOut } from '@/api/books';

const sampleReport: ReportOut = {
  id: 1,
  book: { isbn: '978-7-100-12345-6', title: 'Test', author: 'Test', cover_path: null, report_count: 1 },
  description: 'x',
  upvote: 5,
  downvote: 1,
  created_at: new Date().toISOString(),
  evidences: [],
};

vi.mock('@/api/reports', () => ({
  voteReport: vi.fn(() => Promise.resolve({ data: { ...sampleReport, upvote: 6 } })),
}));

vi.mock('@/stores/fingerprint', () => ({
  useFingerprintStore: () => ({ ensure: () => Promise.resolve('test-fp-12345678') }),
}));

describe('VoteButton', () => {
  it('renders upvote and downvote counts', () => {
    setActivePinia(createPinia());
    const wrapper = mount(VoteButton, { props: { report: sampleReport } });
    expect(wrapper.text()).toContain('5');
    expect(wrapper.text()).toContain('1');
  });
});