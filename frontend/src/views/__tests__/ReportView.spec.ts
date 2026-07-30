import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createMemoryHistory } from 'vue-router';
import ReportView from '../ReportView.vue';

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: 'x' } },
    { path: '/books/:isbn', name: 'book-detail', component: { template: 'x' } },
  ],
});

describe('ReportView', () => {
  it('renders all sections', async () => {
    setActivePinia(createPinia());
    const wrapper = mount(ReportView, {
      global: { plugins: [router] },
    });
    await router.isReady();
    expect(wrapper.text()).toContain('OCR');
    expect(wrapper.text()).toContain('Metadata');
    expect(wrapper.text()).toContain('Attachments');
    expect(wrapper.text()).toContain('FILE REPORT');
  });
});
