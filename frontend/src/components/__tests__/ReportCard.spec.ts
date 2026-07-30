import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { createRouter, createMemoryHistory } from 'vue-router';
import ReportCard from '../ReportCard.vue';
import type { ReportOut } from '@/api/books';

const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/', component: { template: 'x' } }],
});

const sampleReport: ReportOut = {
  id: 1,
  book: { isbn: '978-7-100-12345-6', title: 'Test Book', author: 'Test Author', cover_path: null, report_count: 3 },
  description: 'A very long description that should be truncated to fit within 120 characters limit. '.repeat(5),
  upvote: 5,
  downvote: 1,
  created_at: new Date().toISOString(),
  evidences: [],
};

describe('ReportCard', () => {
  it('renders title, author, isbn', async () => {
    const wrapper = mount(ReportCard, {
      props: { report: sampleReport },
      global: { plugins: [router] },
    });
    await router.isReady();
    expect(wrapper.text()).toContain('Test Book');
    expect(wrapper.text()).toContain('Test Author');
    expect(wrapper.text()).toContain('978-7-100-12345-6');
  });

  it('truncates long descriptions', async () => {
    const wrapper = mount(ReportCard, {
      props: { report: sampleReport },
      global: { plugins: [router] },
    });
    await router.isReady();
    expect(wrapper.text()).toContain('...');
  });
});