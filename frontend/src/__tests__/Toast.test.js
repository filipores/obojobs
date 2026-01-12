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
})
