<template>
  <div class="datetime-picker" ref="pickerRef">
    <div class="datetime-input-wrapper">
      <input
        type="text"
        :value="displayValue"
        @click="togglePicker"
        @keydown="handleKeydown"
        class="form-input datetime-input"
        :placeholder="placeholder"
        readonly
        :aria-label="ariaLabel"
        :aria-expanded="isOpen"
        aria-haspopup="dialog"
      />
      <button
        type="button"
        class="calendar-trigger"
        @click="togglePicker"
        :aria-label="isOpen ? t('components.dateTimePicker.closeCalendar') : t('components.dateTimePicker.openCalendar')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="16" y1="2" x2="16" y2="6"></line>
          <line x1="8" y1="2" x2="8" y2="6"></line>
          <line x1="3" y1="10" x2="21" y2="10"></line>
        </svg>
      </button>
      <button
        v-if="modelValue && clearable"
        type="button"
        class="clear-trigger"
        @click.stop="clearValue"
        :aria-label="t('components.dateTimePicker.clearDate')"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <Teleport to="body">
      <Transition name="picker-fade">
        <div
          v-if="isOpen"
          class="picker-dropdown"
          :style="dropdownStyle"
          role="dialog"
          aria-modal="true"
          aria-label="Datum und Uhrzeit auswaehlen"
        >
          <!-- Calendar Header -->
          <div class="picker-header">
            <button
              type="button"
              class="nav-btn"
              @click="previousMonth"
              aria-label="Vorheriger Monat"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="15,18 9,12 15,6"></polyline>
              </svg>
            </button>
            <span class="month-year">{{ monthYearDisplay }}</span>
            <button
              type="button"
              class="nav-btn"
              @click="nextMonth"
              :aria-label="t('components.dateTimePicker.nextMonth')"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9,6 15,12 9,18"></polyline>
              </svg>
            </button>
          </div>

          <!-- Weekday Headers -->
          <div class="weekdays">
            <span v-for="day in weekdays" :key="day" class="weekday">{{ day }}</span>
          </div>

          <!-- Calendar Days -->
          <div class="calendar-grid">
            <button
              v-for="day in calendarDays"
              :key="day.key"
              type="button"
              :class="[
                'day-btn',
                {
                  'other-month': !day.isCurrentMonth,
                  'today': day.isToday,
                  'selected': day.isSelected
                }
              ]"
              @click="selectDate(day.date)"
              :disabled="!day.isCurrentMonth"
              :aria-label="day.ariaLabel"
              :aria-selected="day.isSelected"
            >
              {{ day.dayNumber }}
            </button>
          </div>

          <!-- Time Picker -->
          <div v-if="showTime" class="time-picker">
            <div class="time-label">Uhrzeit</div>
            <div class="time-inputs">
              <div class="time-input-group">
                <label class="sr-only" for="hour-input">Stunde</label>
                <input
                  id="hour-input"
                  type="number"
                  v-model.number="selectedHour"
                  min="0"
                  max="23"
                  class="time-input"
                  @change="updateTime"
                />
                <span class="time-unit">Std</span>
              </div>
              <span class="time-separator">:</span>
              <div class="time-input-group">
                <label class="sr-only" for="minute-input">Minute</label>
                <input
                  id="minute-input"
                  type="number"
                  v-model.number="selectedMinute"
                  min="0"
                  max="59"
                  step="5"
                  class="time-input"
                  @change="updateTime"
                />
                <span class="time-unit">Min</span>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="picker-footer">
            <button type="button" class="quick-btn" @click="selectToday">Heute</button>
            <button type="button" class="quick-btn" @click="selectTomorrow">Morgen</button>
            <button type="button" class="confirm-btn" @click="confirmSelection">Fertig</button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Datum und Uhrzeit waehlen'
  },
  showTime: {
    type: Boolean,
    default: true
  },
  clearable: {
    type: Boolean,
    default: true
  },
  ariaLabel: {
    type: String,
    default: 'Datum und Uhrzeit'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const pickerRef = ref(null)
const isOpen = ref(false)
const currentMonth = ref(new Date())
const selectedHour = ref(9)
const selectedMinute = ref(0)
const dropdownStyle = ref({})

const weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
const monthNames = [
  'Januar', 'Februar', 'Maerz', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
]

// Parse model value to extract date and time
const parseModelValue = () => {
  if (!props.modelValue) return null
  try {
    return new Date(props.modelValue)
  } catch {
    return null
  }
}

// Initialize from model value
const initFromModelValue = () => {
  const date = parseModelValue()
  if (date && !isNaN(date.getTime())) {
    currentMonth.value = new Date(date.getFullYear(), date.getMonth(), 1)
    selectedHour.value = date.getHours()
    selectedMinute.value = date.getMinutes()
  }
}

// Watch for external changes
watch(() => props.modelValue, initFromModelValue, { immediate: true })

// Display formatted value
const displayValue = computed(() => {
  const date = parseModelValue()
  if (!date || isNaN(date.getTime())) return ''

  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()

  if (props.showTime) {
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    return `${day}.${month}.${year} um ${hour}:${minute} Uhr`
  }

  return `${day}.${month}.${year}`
})

// Month/Year display
const monthYearDisplay = computed(() => {
  return `${monthNames[currentMonth.value.getMonth()]} ${currentMonth.value.getFullYear()}`
})

// Generate calendar days
const calendarDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()

  // First day of month (0 = Sunday, adjust for Monday start)
  const firstDay = new Date(year, month, 1)
  let startDay = firstDay.getDay()
  startDay = startDay === 0 ? 6 : startDay - 1 // Adjust for Monday start

  // Last day of month
  const lastDay = new Date(year, month + 1, 0).getDate()

  // Previous month days to show
  const prevMonthLastDay = new Date(year, month, 0).getDate()

  const days = []
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const selectedDate = parseModelValue()
  const selectedDateOnly = selectedDate ? new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate()) : null

  // Previous month days
  for (let i = startDay - 1; i >= 0; i--) {
    const dayNum = prevMonthLastDay - i
    const date = new Date(year, month - 1, dayNum)
    days.push({
      key: `prev-${dayNum}`,
      dayNumber: dayNum,
      date,
      isCurrentMonth: false,
      isToday: false,
      isSelected: false,
      ariaLabel: `${dayNum}. ${monthNames[month - 1 < 0 ? 11 : month - 1]}`
    })
  }

  // Current month days
  for (let i = 1; i <= lastDay; i++) {
    const date = new Date(year, month, i)
    const dateOnly = new Date(year, month, i)
    dateOnly.setHours(0, 0, 0, 0)

    days.push({
      key: `curr-${i}`,
      dayNumber: i,
      date,
      isCurrentMonth: true,
      isToday: dateOnly.getTime() === today.getTime(),
      isSelected: selectedDateOnly && dateOnly.getTime() === selectedDateOnly.getTime(),
      ariaLabel: `${i}. ${monthNames[month]} ${year}`
    })
  }

  // Next month days to complete grid (6 rows × 7 days = 42)
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const date = new Date(year, month + 1, i)
    days.push({
      key: `next-${i}`,
      dayNumber: i,
      date,
      isCurrentMonth: false,
      isToday: false,
      isSelected: false,
      ariaLabel: `${i}. ${monthNames[month + 1 > 11 ? 0 : month + 1]}`
    })
  }

  return days
})

// Navigation
const previousMonth = () => {
  currentMonth.value = new Date(
    currentMonth.value.getFullYear(),
    currentMonth.value.getMonth() - 1,
    1
  )
}

const nextMonth = () => {
  currentMonth.value = new Date(
    currentMonth.value.getFullYear(),
    currentMonth.value.getMonth() + 1,
    1
  )
}

// Position dropdown
const updateDropdownPosition = async () => {
  await nextTick()
  if (!pickerRef.value) return

  const rect = pickerRef.value.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const dropdownHeight = 420

  const top = rect.bottom + 8
  const wouldOverflow = top + dropdownHeight > viewportHeight

  dropdownStyle.value = {
    position: 'fixed',
    left: `${Math.max(8, rect.left)}px`,
    top: wouldOverflow ? `${rect.top - dropdownHeight - 8}px` : `${top}px`,
    zIndex: 'var(--z-modal)'
  }
}

// Toggle picker
const togglePicker = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    updateDropdownPosition()
  }
}

// Handle keyboard
const handleKeydown = (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    togglePicker()
  } else if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

// Select date
const selectDate = (date) => {
  const newDate = new Date(date)
  if (props.showTime) {
    newDate.setHours(selectedHour.value, selectedMinute.value, 0, 0)
  } else {
    newDate.setHours(0, 0, 0, 0)
  }

  const isoString = newDate.toISOString()
  emit('update:modelValue', isoString)
  emit('change', isoString)
}

// Update time
const updateTime = () => {
  // Clamp values
  selectedHour.value = Math.max(0, Math.min(23, selectedHour.value || 0))
  selectedMinute.value = Math.max(0, Math.min(59, selectedMinute.value || 0))

  const currentDate = parseModelValue()
  if (currentDate && !isNaN(currentDate.getTime())) {
    currentDate.setHours(selectedHour.value, selectedMinute.value, 0, 0)
    const isoString = currentDate.toISOString()
    emit('update:modelValue', isoString)
    emit('change', isoString)
  }
}

// Quick selections
const selectToday = () => {
  const today = new Date()
  today.setHours(selectedHour.value, selectedMinute.value, 0, 0)
  currentMonth.value = new Date(today.getFullYear(), today.getMonth(), 1)
  const isoString = today.toISOString()
  emit('update:modelValue', isoString)
  emit('change', isoString)
}

const selectTomorrow = () => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(selectedHour.value, selectedMinute.value, 0, 0)
  currentMonth.value = new Date(tomorrow.getFullYear(), tomorrow.getMonth(), 1)
  const isoString = tomorrow.toISOString()
  emit('update:modelValue', isoString)
  emit('change', isoString)
}

// Confirm and close
const confirmSelection = () => {
  isOpen.value = false
}

// Clear value
const clearValue = () => {
  emit('update:modelValue', '')
  emit('change', '')
}

// Click outside handler
const handleClickOutside = (e) => {
  if (isOpen.value && pickerRef.value && !pickerRef.value.contains(e.target)) {
    // Check if click is inside dropdown
    const dropdown = document.querySelector('.picker-dropdown')
    if (!dropdown || !dropdown.contains(e.target)) {
      isOpen.value = false
    }
  }
}

// Resize handler
const handleResize = () => {
  if (isOpen.value) {
    updateDropdownPosition()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', handleResize)
  window.addEventListener('scroll', handleResize, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('scroll', handleResize, true)
})
</script>

<style scoped>
.datetime-picker {
  position: relative;
  width: 100%;
}

.datetime-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.datetime-input {
  padding-right: 4.5rem;
  cursor: pointer;
  background: var(--color-bg-elevated);
}

.calendar-trigger {
  position: absolute;
  right: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.375rem;
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-subtle);
}

.calendar-trigger:hover {
  color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.clear-trigger {
  position: absolute;
  right: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  background: none;
  border: none;
  color: var(--color-text-ghost);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-subtle);
}

.clear-trigger:hover {
  color: var(--color-error);
  background: var(--color-error-light);
}

/* Dropdown */
.picker-dropdown {
  width: 320px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-floating);
  padding: var(--space-md);
  font-family: var(--font-body);
}

/* Header */
.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.month-year {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-text-primary);
  letter-spacing: var(--tracking-normal);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-subtle);
}

.nav-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
  background: var(--color-ai-subtle);
}

/* Weekdays */
.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0;
  margin-bottom: var(--space-xs);
}

.weekday {
  text-align: center;
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  padding: var(--space-xs) 0;
}

/* Calendar Grid */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.day-btn {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-subtle);
}

.day-btn:hover:not(:disabled) {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.day-btn.other-month {
  color: var(--color-text-ghost);
  opacity: 0.4;
}

.day-btn.today {
  font-weight: 600;
  color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.day-btn.selected {
  background: var(--color-ai);
  color: var(--color-text-inverse);
  font-weight: 500;
}

.day-btn.selected:hover {
  background: var(--color-ai-dark);
  color: var(--color-text-inverse);
}

/* Time Picker */
.time-picker {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.time-label {
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.time-inputs {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.time-input-group {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.time-input {
  width: 60px;
  padding: var(--space-sm);
  font-size: 1rem;
  font-family: var(--font-body);
  text-align: center;
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  transition: all var(--transition-subtle);
}

.time-input:focus {
  outline: none;
  border-color: var(--color-ai);
  box-shadow: 0 0 0 3px var(--color-ai-subtle);
}

.time-unit {
  font-size: 0.75rem;
  color: var(--color-text-ghost);
}

.time-separator {
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
}

/* Footer */
.picker-footer {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border-light);
}

.quick-btn {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  font-size: 0.8125rem;
  font-family: var(--font-body);
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-subtle);
}

.quick-btn:hover {
  border-color: var(--color-ai);
  color: var(--color-ai);
  background: var(--color-ai-subtle);
}

.confirm-btn {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  font-size: 0.8125rem;
  font-family: var(--font-body);
  font-weight: 500;
  background: var(--color-ai);
  border: 1px solid var(--color-ai);
  border-radius: var(--radius-sm);
  color: var(--color-text-inverse);
  cursor: pointer;
  transition: all var(--transition-subtle);
}

.confirm-btn:hover {
  background: var(--color-ai-dark);
  border-color: var(--color-ai-dark);
}

/* Screen reader only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Transition */
.picker-fade-enter-active,
.picker-fade-leave-active {
  transition: opacity 200ms var(--ease-zen), transform 200ms var(--ease-zen);
}

.picker-fade-enter-from,
.picker-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Mobile */
@media (max-width: 480px) {
  .picker-dropdown {
    width: calc(100vw - 16px);
    max-width: 360px;
    left: 8px !important;
    right: 8px;
  }
}
</style>
