import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import { createRouter, createMemoryHistory } from 'vue-router';
import SearchBox from '../SearchBox.vue';

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: 'x' } },
    { path: '/search', name: 'search', component: { template: 'x' } },
  ],
});

describe('SearchBox', () => {
  it('emits update:modelValue on input', async () => {
    const wrapper = mount(SearchBox, {
      props: { modelValue: '' },
      global: { plugins: [router] },
    });
    await router.isReady();
    const input = wrapper.find('input');
    await input.setValue('hello');
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['hello']);
  });

  it('emits search after debounce', async () => {
    vi.useFakeTimers();
    const wrapper = mount(SearchBox, {
      props: { modelValue: '' },
      global: { plugins: [router] },
    });
    await router.isReady();
    await wrapper.find('input').setValue('test');
    vi.advanceTimersByTime(350);
    expect(wrapper.emitted('search')?.[0]).toEqual(['test']);
    vi.useRealTimers();
  });

  it('triggers router push on enter', async () => {
    const wrapper = mount(SearchBox, {
      props: { modelValue: 'foo' },
      global: { plugins: [router] },
    });
    await router.isReady();
    const pushSpy = vi.spyOn(router, 'push');
    await wrapper.find('input').trigger('keyup.enter');
    expect(pushSpy).toHaveBeenCalledWith({ name: 'search', query: { q: 'foo' } });
  });
});