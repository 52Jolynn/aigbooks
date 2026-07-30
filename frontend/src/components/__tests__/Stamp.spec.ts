import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import Stamp from '../Stamp.vue';

describe('Stamp', () => {
  it('renders featured size with count', () => {
    const wrapper = mount(Stamp, {
      props: { count: 14, size: 'featured' },
    });
    expect(wrapper.classes()).toContain('stamp--featured');
    expect(wrapper.text()).toContain('× 14');
  });

  it('renders mini size', () => {
    const wrapper = mount(Stamp, { props: { count: 9, size: 'mini' } });
    expect(wrapper.classes()).toContain('stamp--mini');
  });

  it('exposes pulse method', () => {
    const wrapper = mount(Stamp, { props: { count: 1 } });
    expect(typeof wrapper.vm.pulse).toBe('function');
  });
});