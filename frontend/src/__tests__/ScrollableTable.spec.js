import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ScrollableTable from '../components/ScrollableTable.vue'

describe('ScrollableTable', () => {
  let wrapper
  let mockResizeObserver

  beforeEach(() => {
    // Mock ResizeObserver
    mockResizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn()
    }))
    window.ResizeObserver = mockResizeObserver
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.restoreAllMocks()
  })

  it('renders slot content', () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<table><tr><td>Test Content</td></tr></table>'
      }
    })

    expect(wrapper.html()).toContain('Test Content')
    expect(wrapper.find('table').exists()).toBe(true)
  })

  it('has scrollable container class', () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div>Content</div>'
      }
    })

    expect(wrapper.find('.scrollable-table-container').exists()).toBe(true)
    expect(wrapper.find('.scrollable-table-inner').exists()).toBe(true)
  })

  it('does not show scroll indicators initially when content fits', async () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div>Short content</div>'
      }
    })

    // Wait for component to mount and check scroll state
    await wrapper.vm.$nextTick()

    // By default, without actual scrollable content, indicators should be hidden
    expect(wrapper.find('.scroll-indicator-left').exists()).toBe(false)
    expect(wrapper.find('.scroll-indicator-right').exists()).toBe(false)
  })

  it('has correct aria-labels on scroll buttons when visible', async () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div style="width: 2000px;">Wide content</div>'
      }
    })

    // Mock scroll state to show buttons
    wrapper.vm.canScrollRight = true
    await wrapper.vm.$nextTick()

    const rightButton = wrapper.find('.scroll-indicator-right')
    expect(rightButton.exists()).toBe(true)
    expect(rightButton.attributes('aria-label')).toBe('Nach rechts scrollen')

    wrapper.vm.canScrollLeft = true
    await wrapper.vm.$nextTick()

    const leftButton = wrapper.find('.scroll-indicator-left')
    expect(leftButton.exists()).toBe(true)
    expect(leftButton.attributes('aria-label')).toBe('Nach links scrollen')
  })

  it('exposes updateScrollState method', () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div>Content</div>'
      }
    })

    expect(typeof wrapper.vm.updateScrollState).toBe('function')
  })

  it('applies can-scroll classes based on scroll state', async () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div>Content</div>'
      }
    })

    // Initially no scroll classes
    expect(wrapper.find('.scrollable-table-container').classes()).not.toContain('can-scroll-left')
    expect(wrapper.find('.scrollable-table-container').classes()).not.toContain('can-scroll-right')

    // Set scroll states
    wrapper.vm.canScrollLeft = true
    wrapper.vm.canScrollRight = true
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.scrollable-table-container').classes()).toContain('can-scroll-left')
    expect(wrapper.find('.scrollable-table-container').classes()).toContain('can-scroll-right')
  })

  it('scroll buttons call scrollBy when clicked', async () => {
    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div>Content</div>'
      },
      attachTo: document.body
    })

    // Make buttons visible by setting reactive state
    wrapper.vm.canScrollLeft = true
    wrapper.vm.canScrollRight = true
    await wrapper.vm.$nextTick()

    // Mock scrollBy on the container
    const scrollContainer = wrapper.find('.scrollable-table-inner').element
    scrollContainer.scrollBy = vi.fn()

    // Now find buttons after they're rendered
    const rightButton = wrapper.find('.scroll-indicator-right')
    const leftButton = wrapper.find('.scroll-indicator-left')

    expect(rightButton.exists()).toBe(true)
    expect(leftButton.exists()).toBe(true)

    // Click right button
    await rightButton.trigger('click')
    expect(scrollContainer.scrollBy).toHaveBeenCalledWith({
      left: 200,
      behavior: 'smooth'
    })

    // Click left button
    await leftButton.trigger('click')
    expect(scrollContainer.scrollBy).toHaveBeenCalledWith({
      left: -200,
      behavior: 'smooth'
    })
  })

  it('creates ResizeObserver when available', async () => {
    // Reset the mock to track new calls
    mockResizeObserver.mockClear()

    wrapper = mount(ScrollableTable, {
      slots: {
        default: '<div>Content</div>'
      },
      attachTo: document.body
    })

    // Wait for onMounted and nextTick
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    // ResizeObserver should be instantiated during mount
    expect(mockResizeObserver).toHaveBeenCalled()
  })
})
