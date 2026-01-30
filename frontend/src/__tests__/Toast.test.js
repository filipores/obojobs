import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Toast from '../components/Toast.vue'

describe('Toast.vue', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('rendering', () => {
    it('renders empty container when no toasts', () => {
      const wrapper = mount(Toast)
      expect(wrapper.find('.toast-container').exists()).toBe(true)
      expect(wrapper.findAll('.toast')).toHaveLength(0)
    })

    it('renders toast when added via exposed method', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Test message', 'success')
      await wrapper.vm.$nextTick()

      const toasts = wrapper.findAll('.toast')
      expect(toasts).toHaveLength(1)
      expect(toasts[0].classes()).toContain('success')
      expect(toasts[0].find('.toast-message').text()).toBe('Test message')
    })

    it('renders correct icon for each toast type', async () => {
      const wrapper = mount(Toast)

      wrapper.vm.add('Success', 'success')
      wrapper.vm.add('Error', 'error')
      wrapper.vm.add('Warning', 'warning')
      wrapper.vm.add('Info', 'info')
      await wrapper.vm.$nextTick()

      const toasts = wrapper.findAll('.toast')
      expect(toasts[0].find('.toast-icon').text()).toBe('✓')
      expect(toasts[1].find('.toast-icon').text()).toBe('✗')
      expect(toasts[2].find('.toast-icon').text()).toBe('⚠')
      expect(toasts[3].find('.toast-icon').text()).toBe('ⓘ')
    })

    it('renders default info icon for unknown type', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Unknown type', 'unknown')
      await wrapper.vm.$nextTick()

      const toast = wrapper.find('.toast')
      expect(toast.find('.toast-icon').text()).toBe('ⓘ')
    })
  })

  describe('interaction', () => {
    it('removes toast when close button is clicked', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Test message', 'info', 0) // duration 0 = no auto-remove
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.toast')).toHaveLength(1)

      await wrapper.find('.toast-close').trigger('click')
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.toast')).toHaveLength(0)
    })

    it('auto-removes toast after duration', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Auto remove', 'info', 3000)
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.toast')).toHaveLength(1)

      vi.advanceTimersByTime(3000)
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.toast')).toHaveLength(0)
    })

    it('does not auto-remove when duration is 0', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Persistent', 'info', 0)
      await wrapper.vm.$nextTick()

      vi.advanceTimersByTime(10000)
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.toast')).toHaveLength(1)
    })
  })

  describe('multiple toasts', () => {
    it('can display multiple toasts', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('First', 'success', 0)
      wrapper.vm.add('Second', 'error', 0)
      wrapper.vm.add('Third', 'warning', 0)
      await wrapper.vm.$nextTick()

      expect(wrapper.findAll('.toast')).toHaveLength(3)
    })

    it('removes only the clicked toast', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('First', 'success', 0)
      vi.advanceTimersByTime(1) // Ensure different timestamp for next toast
      wrapper.vm.add('Second', 'error', 0)
      await wrapper.vm.$nextTick()

      const closeButtons = wrapper.findAll('.toast-close')
      await closeButtons[0].trigger('click')
      await wrapper.vm.$nextTick()

      const remainingToasts = wrapper.findAll('.toast')
      expect(remainingToasts).toHaveLength(1)
      expect(remainingToasts[0].find('.toast-message').text()).toBe('Second')
    })
  })

  describe('deduplication', () => {
    it('deduplicates exact same message within 2 second window', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Same message', 'error', 0)
      wrapper.vm.add('Same message', 'error', 0)
      await wrapper.vm.$nextTick()

      // Should only show one toast due to deduplication
      expect(wrapper.findAll('.toast')).toHaveLength(1)
    })

    it('allows same message after 2 second window expires', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Same message', 'error', 0)
      await wrapper.vm.$nextTick()

      // Advance time past the 2 second deduplication window
      vi.advanceTimersByTime(2100)

      wrapper.vm.add('Same message', 'error', 0)
      await wrapper.vm.$nextTick()

      // Should show both toasts now
      expect(wrapper.findAll('.toast')).toHaveLength(2)
    })

    it('deduplicates similar messages with common error keywords', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Fehler aufgetreten', 'error', 0)
      wrapper.vm.add('Fehler beim Laden', 'error', 0)
      await wrapper.vm.$nextTick()

      // Should only show one toast (similar short error messages)
      expect(wrapper.findAll('.toast')).toHaveLength(1)
    })

    it('deduplicates messages where one contains the other', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Fehler', 'error', 0)
      wrapper.vm.add('Fehler beim Speichern', 'error', 0)
      await wrapper.vm.$nextTick()

      // Should only show one toast
      expect(wrapper.findAll('.toast')).toHaveLength(1)
    })

    it('allows different types of same message', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Same message', 'error', 0)
      wrapper.vm.add('Same message', 'success', 0)
      await wrapper.vm.$nextTick()

      // Should show both (different types)
      expect(wrapper.findAll('.toast')).toHaveLength(2)
    })

    it('allows genuinely different messages', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('First unique message about documents', 'info', 0)
      wrapper.vm.add('Second unique message about templates', 'info', 0)
      await wrapper.vm.$nextTick()

      // Should show both (different messages)
      expect(wrapper.findAll('.toast')).toHaveLength(2)
    })

    it('normalizes messages by removing punctuation and whitespace', async () => {
      const wrapper = mount(Toast)
      wrapper.vm.add('Same message!', 'error', 0)
      wrapper.vm.add('Same   message', 'error', 0)
      await wrapper.vm.$nextTick()

      // Should only show one (normalized to same)
      expect(wrapper.findAll('.toast')).toHaveLength(1)
    })
  })
})
