import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import FormField from '../FormField.vue';

describe('FormField', () => {
  it('renders label and input', () => {
    const wrapper = mount(FormField, {
      props: { label: 'ISBN', modelValue: '' },
    });
    expect(wrapper.text()).toContain('ISBN');
  });

  it('emits update:modelValue on input', async () => {
    const wrapper = mount(FormField, {
      props: { label: 'ISBN', modelValue: '' },
    });
    await wrapper.find('input').setValue('1234567890');
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['1234567890']);
  });

  it('shows error message', () => {
    const wrapper = mount(FormField, {
      props: { label: 'ISBN', modelValue: '', error: 'Invalid ISBN' },
    });
    expect(wrapper.text()).toContain('Invalid ISBN');
  });
});