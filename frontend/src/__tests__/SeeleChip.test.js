import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SeeleChip from '../components/seele/SeeleChip.vue'

describe('SeeleChip', () => {
  it('renders label text', () => {
    const wrapper = mount(SeeleChip, {
      props: { label: 'Teamarbeit', value: 'teamarbeit' }
    })
    expect(wrapper.text()).toBe('Teamarbeit')
  })

  it('emits toggle with value on click', async () => {
    const wrapper = mount(SeeleChip, {
      props: { label: 'Kreativitaet', value: 'kreativ' }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('toggle')).toBeTruthy()
    expect(wrapper.emitted('toggle')[0]).toEqual(['kreativ'])
  })

  it('emits toggle with label when no value provided', async () => {
    const wrapper = mount(SeeleChip, {
      props: { label: 'Teamarbeit' }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('toggle')[0]).toEqual(['Teamarbeit'])
  })

  it('applies selected class when isSelected', () => {
    const wrapper = mount(SeeleChip, {
      props: { label: 'Test', value: 'test', isSelected: true }
    })
    expect(wrapper.find('.seele-chip--selected').exists()).toBe(true)
  })

  it('does not apply selected class when not selected', () => {
    const wrapper = mount(SeeleChip, {
      props: { label: 'Test', value: 'test', isSelected: false }
    })
    expect(wrapper.find('.seele-chip--selected').exists()).toBe(false)
  })
})
