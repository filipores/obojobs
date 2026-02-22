import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SeeleFrage from '../components/seele/SeeleFrage.vue'

const chipsFrage = {
  key: 'arbeitsweise',
  frage: 'Wie arbeitest du am liebsten?',
  typ: 'chips',
  optionen: ['Allein', 'Im Team', 'Beides'],
  mehrfach: false
}

const multiChipsFrage = {
  key: 'staerken',
  frage: 'Was sind deine Staerken?',
  typ: 'chips',
  optionen: ['Analytisch', 'Kreativ', 'Kommunikativ', 'Organisiert'],
  mehrfach: true,
  max_auswahl: 3
}

const freitextFrage = {
  key: 'motivation',
  frage: 'Was motiviert dich?',
  typ: 'freitext'
}

const sliderFrage = {
  key: 'erfahrung',
  frage: 'Wie viele Jahre Erfahrung hast du?',
  typ: 'slider',
  min_wert: 0,
  max_wert: 20,
  schritt: 1
}

const defaultFortschritt = { aktuell: 1, gesamt: 5 }

describe('SeeleFrage', () => {
  it('renders question text', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: chipsFrage, fortschritt: defaultFortschritt }
    })
    expect(wrapper.find('.frage-text').text()).toBe('Wie arbeitest du am liebsten?')
  })

  it('renders chips for options', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: chipsFrage, fortschritt: defaultFortschritt }
    })
    const chips = wrapper.findAll('.seele-chip')
    expect(chips.length).toBe(3)
    expect(chips[0].text()).toBe('Allein')
  })

  it('renders progress dots', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: chipsFrage, fortschritt: { aktuell: 2, gesamt: 5 } }
    })
    const dots = wrapper.findAll('.progress-dot')
    expect(dots.length).toBe(5)
    expect(dots[0].classes()).toContain('progress-dot--done')
    expect(dots[1].classes()).toContain('progress-dot--current')
  })

  it('emits antwort on submit with single selection', async () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: chipsFrage, fortschritt: defaultFortschritt }
    })
    // Click a chip
    await wrapper.findAll('.seele-chip')[1].trigger('click')
    // Click Weiter
    await wrapper.find('.zen-btn-ai').trigger('click')
    expect(wrapper.emitted('antwort')).toBeTruthy()
    expect(wrapper.emitted('antwort')[0][0]).toEqual({
      frage_key: 'arbeitsweise',
      antwort: 'Im Team'
    })
  })

  it('supports multi-select chips', async () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: multiChipsFrage, fortschritt: defaultFortschritt }
    })
    await wrapper.findAll('.seele-chip')[0].trigger('click')
    await wrapper.findAll('.seele-chip')[2].trigger('click')
    await wrapper.find('.zen-btn-ai').trigger('click')
    expect(wrapper.emitted('antwort')[0][0]).toEqual({
      frage_key: 'staerken',
      antwort: ['Analytisch', 'Kommunikativ']
    })
  })

  it('emits ueberspringen on skip', async () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: chipsFrage, fortschritt: defaultFortschritt }
    })
    await wrapper.find('.skip-link').trigger('click')
    expect(wrapper.emitted('ueberspringen')).toBeTruthy()
    expect(wrapper.emitted('ueberspringen')[0]).toEqual(['arbeitsweise'])
  })

  it('renders freitext textarea', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: freitextFrage, fortschritt: defaultFortschritt }
    })
    expect(wrapper.find('.freitext-textarea').exists()).toBe(true)
  })

  it('renders slider input', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: sliderFrage, fortschritt: defaultFortschritt }
    })
    expect(wrapper.find('.slider-input').exists()).toBe(true)
  })

  it('disables submit when no selection for chips', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: chipsFrage, fortschritt: defaultFortschritt }
    })
    expect(wrapper.find('.zen-btn-ai').attributes('disabled')).toBeDefined()
  })

  it('enables submit for slider type always', () => {
    const wrapper = mount(SeeleFrage, {
      props: { frage: sliderFrage, fortschritt: defaultFortschritt }
    })
    expect(wrapper.find('.zen-btn-ai').attributes('disabled')).toBeUndefined()
  })
})
