import { ref, h, render } from 'vue'
import ConfirmModal from '@/components/ConfirmModal.vue'

// Singleton state for the confirm modal
const confirmState = ref({
  visible: false,
  title: 'Bestätigung',
  message: '',
  confirmText: 'Bestätigen',
  cancelText: 'Abbrechen',
  type: 'default',
  showCheckbox: false,
  checkboxLabel: '',
  checkboxDefault: false,
  resolve: null
})

let containerEl = null

/**
 * Show a confirmation dialog and return a Promise that resolves to true (confirmed) or false (cancelled)
 *
 * @param {Object|string} options - Options object or message string
 * @param {string} options.title - Modal title (default: 'Bestätigung')
 * @param {string} options.message - Message to display (required)
 * @param {string} options.confirmText - Confirm button text (default: 'Bestätigen')
 * @param {string} options.cancelText - Cancel button text (default: 'Abbrechen')
 * @param {string} options.type - 'default' or 'danger' (default: 'default')
 * @param {boolean} options.showCheckbox - Show a checkbox option (default: false)
 * @param {string} options.checkboxLabel - Label for the checkbox
 * @param {boolean} options.checkboxDefault - Default checkbox state (default: false)
 * @returns {Promise<boolean|{confirmed: boolean, checkboxChecked: boolean}>} - Resolves to true/false or object with checkbox state
 *
 * @example
 * // Simple usage
 * const confirmed = await confirm('Sind Sie sicher?')
 *
 * @example
 * // With options
 * const confirmed = await confirm({
 *   title: 'Löschen bestätigen',
 *   message: 'Möchten Sie diesen Eintrag wirklich löschen?',
 *   confirmText: 'Löschen',
 *   cancelText: 'Abbrechen',
 *   type: 'danger'
 * })
 *
 * @example
 * // With checkbox
 * const result = await confirm({
 *   title: 'Dokument löschen',
 *   message: 'Möchten Sie dieses Dokument wirklich löschen?',
 *   showCheckbox: true,
 *   checkboxLabel: 'Auch extrahierte Skills löschen',
 *   type: 'danger'
 * })
 * // result = { confirmed: true, checkboxChecked: true }
 */
export function confirm(options) {
  return new Promise((resolve) => {
    // Normalize options
    const opts = typeof options === 'string' ? { message: options } : options
    const hasCheckbox = opts.showCheckbox || false

    // Update state
    confirmState.value = {
      visible: true,
      title: opts.title || 'Bestätigung',
      message: opts.message,
      confirmText: opts.confirmText || 'Bestätigen',
      cancelText: opts.cancelText || 'Abbrechen',
      type: opts.type || 'default',
      showCheckbox: hasCheckbox,
      checkboxLabel: opts.checkboxLabel || '',
      checkboxDefault: opts.checkboxDefault || false,
      resolve,
      hasCheckbox
    }

    // Create container if it doesn't exist
    if (!containerEl) {
      containerEl = document.createElement('div')
      containerEl.id = 'confirm-modal-container'
      document.body.appendChild(containerEl)
    }

    // Render the modal
    const vnode = h(ConfirmModal, {
      visible: confirmState.value.visible,
      title: confirmState.value.title,
      message: confirmState.value.message,
      confirmText: confirmState.value.confirmText,
      cancelText: confirmState.value.cancelText,
      type: confirmState.value.type,
      showCheckbox: confirmState.value.showCheckbox,
      checkboxLabel: confirmState.value.checkboxLabel,
      checkboxDefault: confirmState.value.checkboxDefault,
      'onUpdate:visible': (val) => {
        confirmState.value.visible = val
      },
      onConfirm: (payload) => {
        if (confirmState.value.hasCheckbox) {
          confirmState.value.resolve?.({ confirmed: true, checkboxChecked: payload?.checkboxChecked || false })
        } else {
          confirmState.value.resolve?.(true)
        }
        cleanup()
      },
      onCancel: () => {
        if (confirmState.value.hasCheckbox) {
          confirmState.value.resolve?.({ confirmed: false, checkboxChecked: false })
        } else {
          confirmState.value.resolve?.(false)
        }
        cleanup()
      }
    })

    render(vnode, containerEl)
  })
}

function cleanup() {
  if (containerEl) {
    render(null, containerEl)
  }
  confirmState.value = {
    visible: false,
    title: 'Bestätigung',
    message: '',
    confirmText: 'Bestätigen',
    cancelText: 'Abbrechen',
    type: 'default',
    showCheckbox: false,
    checkboxLabel: '',
    checkboxDefault: false,
    resolve: null,
    hasCheckbox: false
  }
}

/**
 * Composable hook for using confirm dialog in Vue components
 * Returns the confirm function
 */
export function useConfirm() {
  return { confirm }
}

export default useConfirm
