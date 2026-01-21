import { createI18n } from 'vue-i18n'
import de from './locales/de.json'
import en from './locales/en.json'

// Get saved locale from localStorage or default to 'de'
function getInitialLocale() {
  const savedLocale = localStorage.getItem('obojobs-locale')
  if (savedLocale && ['de', 'en'].includes(savedLocale)) {
    return savedLocale
  }

  // Check browser language preference
  const browserLang = navigator.language?.split('-')[0]
  if (browserLang === 'en') {
    return 'en'
  }

  // Default to German
  return 'de'
}

const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: getInitialLocale(),
  fallbackLocale: 'de',
  messages: {
    de,
    en
  }
})

// Helper to change locale and persist
export function setLocale(locale) {
  if (!['de', 'en'].includes(locale)) return

  i18n.global.locale.value = locale
  localStorage.setItem('obojobs-locale', locale)
  document.documentElement.lang = locale
}

// Helper to get current locale
export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
