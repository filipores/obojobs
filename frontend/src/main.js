import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './assets/styles.css'

// Set initial document language based on saved preference
const savedLocale = localStorage.getItem('obojobs-locale') || 'de'
document.documentElement.lang = savedLocale

createApp(App).use(router).use(i18n).mount('#app')
