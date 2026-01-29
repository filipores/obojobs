<template>
  <div class="language-switcher" ref="switcherRef">
    <button
      @click="toggleDropdown"
      class="language-toggle nav-icon"
      :title="$t('language.select')"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <path d="M2 12h20"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span class="current-lang">{{ currentLocale.toUpperCase() }}</span>
    </button>

    <Transition name="dropdown">
      <div v-if="isOpen" class="language-dropdown" role="listbox" :aria-label="$t('language.select')">
        <button
          v-for="lang in languages"
          :key="lang.code"
          @click="selectLanguage(lang.code)"
          class="language-option"
          :class="{ active: currentLocale === lang.code }"
          role="option"
          :aria-selected="currentLocale === lang.code"
        >
          <span class="lang-flag">{{ lang.flag }}</span>
          <span class="lang-name">{{ lang.name }}</span>
          <svg v-if="currentLocale === lang.code" class="check-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '../i18n'
import { authStore } from '../store/auth'
import api from '../api/client'

const { locale } = useI18n()

const isOpen = ref(false)
const switcherRef = ref(null)

const languages = [
  { code: 'de', name: 'Deutsch', flag: 'DE' },
  { code: 'en', name: 'English', flag: 'EN' }
]

const currentLocale = computed(() => locale.value)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectLanguage = async (langCode) => {
  if (langCode === currentLocale.value) {
    isOpen.value = false
    return
  }

  // Update vue-i18n locale
  setLocale(langCode)

  // If authenticated, persist to backend
  if (authStore.isAuthenticated()) {
    try {
      await api.silent.put('/auth/language', { language: langCode })
    } catch (error) {
      console.warn('Failed to save language preference:', error)
    }
  }

  isOpen.value = false
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (switcherRef.value && !switcherRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

// Close dropdown on escape key
const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.language-toggle:hover {
  color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.current-lang {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.05em;
}

.language-dropdown {
  position: absolute;
  top: calc(100% + var(--space-xs));
  right: 0;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lifted);
  min-width: 140px;
  z-index: var(--z-dropdown);
  overflow: hidden;
}

.language-option {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-primary);
  font-size: 0.875rem;
  text-align: left;
  transition: background var(--transition-base);
}

.language-option:hover {
  background: var(--color-bg-hover);
}

.language-option.active {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.lang-flag {
  font-weight: 600;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  min-width: 24px;
}

.lang-name {
  flex: 1;
}

.check-icon {
  color: var(--color-ai);
  flex-shrink: 0;
}

/* Dropdown animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s var(--ease-out);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Mobile adjustments */
@media (max-width: 768px) {
  .current-lang {
    display: none;
  }

  .language-dropdown {
    right: auto;
    left: 50%;
    transform: translateX(-50%);
  }
}
</style>
