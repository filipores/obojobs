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
 * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
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
 */
export function confirm(options) {
  return new Promise((resolve) => {
    // Normalize options
    const opts = typeof options === 'string' ? { message: options } : options

    // Update state
    confirmState.value = {
      visible: true,
      title: opts.title || 'Bestätigung',
      message: opts.message,
      confirmText: opts.confirmText || 'Bestätigen',
      cancelText: opts.cancelText || 'Abbrechen',
      type: opts.type || 'default',
      resolve
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
      'onUpdate:visible': (val) => {
        confirmState.value.visible = val
      },
      onConfirm: () => {
        confirmState.value.resolve?.(true)
        cleanup()
      },
      onCancel: () => {
        confirmState.value.resolve?.(false)
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
    resolve: null
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
