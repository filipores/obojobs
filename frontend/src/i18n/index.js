import { createI18n } from 'vue-i18n'
import de from './locales/de.json'
import en from './locales/en.json'

const i18n = createI18n({
  legacy: false,
  locale: 'de',
  fallbackLocale: 'en',
  messages: {
    de,
    en
  }
})

export default i18n

export function useI18n() {
  return i18n.global
}

export function t(key, params) {
  return i18n.global.t(key, params)
}
