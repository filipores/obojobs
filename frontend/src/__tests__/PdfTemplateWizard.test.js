import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PdfUploadStep from '../components/PdfTemplateWizard/PdfUploadStep.vue'
import VariableReviewStep from '../components/PdfTemplateWizard/VariableReviewStep.vue'

// Mock File constructor for tests
function createMockFile(name, size, type = 'application/pdf') {
  const file = new File(['x'.repeat(size)], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('PdfUploadStep.vue', () => {
  describe('rendering', () => {
    it('renders drop zone in empty state', () => {
      const wrapper = mount(PdfUploadStep)
      expect(wrapper.find('.drop-zone').exists()).toBe(true)
      expect(wrapper.find('.drop-zone-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('Klicken')
      expect(wrapper.text()).toContain('PDF hierher ziehen')
    })

    it('renders file requirements list', () => {
      const wrapper = mount(PdfUploadStep)
      expect(wrapper.find('.upload-requirements').exists()).toBe(true)
      expect(wrapper.text()).toContain('PDF-Format')
      expect(wrapper.text()).toContain('10 MB')
    })

    it('does not show error message initially', () => {
      const wrapper = mount(PdfUploadStep)
      expect(wrapper.find('.upload-error').exists()).toBe(false)
    })
  })

  describe('file validation', () => {
    it('accepts valid PDF file', async () => {
      const wrapper = mount(PdfUploadStep)
      const file = createMockFile('test.pdf', 1024, 'application/pdf')

      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.emitted('file-selected')).toBeTruthy()
      expect(wrapper.emitted('file-selected')[0][0]).toBe(file)
      expect(wrapper.find('.file-name').text()).toBe('test.pdf')
    })

    it('rejects non-PDF file', async () => {
      const wrapper = mount(PdfUploadStep)
      const file = createMockFile('test.txt', 1024, 'text/plain')

      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.find('.upload-error').exists()).toBe(true)
      expect(wrapper.text()).toContain('PDF-Datei')
      expect(wrapper.emitted('file-selected')).toBeFalsy()
    })

    it('rejects file larger than 10 MB', async () => {
      const wrapper = mount(PdfUploadStep)
      const file = createMockFile('large.pdf', 11 * 1024 * 1024, 'application/pdf')

      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.find('.upload-error').exists()).toBe(true)
      expect(wrapper.text()).toContain('zu gross')
    })

    it('rejects empty file', async () => {
      const wrapper = mount(PdfUploadStep)
      const file = createMockFile('empty.pdf', 0, 'application/pdf')

      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.find('.upload-error').exists()).toBe(true)
      expect(wrapper.text()).toContain('leer')
    })

    it('accepts PDF by extension even without correct MIME type', async () => {
      const wrapper = mount(PdfUploadStep)
      // Some systems report different MIME types
      const file = createMockFile('document.pdf', 1024, 'application/octet-stream')

      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.emitted('file-selected')).toBeTruthy()
    })
  })

  describe('drag and drop', () => {
    it('shows drag-over state on dragenter', async () => {
      const wrapper = mount(PdfUploadStep)
      const dropZone = wrapper.find('.drop-zone')

      await dropZone.trigger('dragenter')

      expect(wrapper.find('.drop-zone.drag-over').exists()).toBe(true)
    })

    it('removes drag-over state on dragleave', async () => {
      const wrapper = mount(PdfUploadStep)
      const dropZone = wrapper.find('.drop-zone')

      await dropZone.trigger('dragenter')
      expect(wrapper.find('.drop-zone.drag-over').exists()).toBe(true)

      // Simulate leaving the drop zone entirely
      await dropZone.trigger('dragleave', {
        relatedTarget: document.body
      })

      expect(wrapper.find('.drop-zone.drag-over').exists()).toBe(false)
    })

    it('handles file drop', async () => {
      const wrapper = mount(PdfUploadStep)
      const dropZone = wrapper.find('.drop-zone')
      const file = createMockFile('dropped.pdf', 1024, 'application/pdf')

      await dropZone.trigger('drop', {
        dataTransfer: {
          files: [file]
        }
      })

      expect(wrapper.emitted('file-selected')).toBeTruthy()
      expect(wrapper.emitted('file-selected')[0][0]).toBe(file)
    })
  })

  describe('file removal', () => {
    it('removes selected file when remove button clicked', async () => {
      const wrapper = mount(PdfUploadStep)
      const file = createMockFile('test.pdf', 1024, 'application/pdf')

      // First select a file
      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.find('.file-name').exists()).toBe(true)

      // Click remove button
      await wrapper.find('.file-remove').trigger('click')

      expect(wrapper.find('.file-name').exists()).toBe(false)
      expect(wrapper.emitted('file-selected').pop()[0]).toBeNull()
    })
  })

  describe('file size formatting', () => {
    it('displays file size correctly', async () => {
      const wrapper = mount(PdfUploadStep)
      const file = createMockFile('test.pdf', 1536, 'application/pdf') // 1.5 KB

      const input = wrapper.find('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file]
      })
      await input.trigger('change')

      expect(wrapper.find('.file-size').text()).toContain('KB')
    })
  })
})

describe('VariableReviewStep.vue', () => {
  const createSuggestions = () => [
    {
      id: '1',
      variable_name: 'FIRMA',
      suggested_text: 'Muster GmbH',
      reason: 'Company name detected',
      position: { page: 1, line: 5 },
      status: 'pending'
    },
    {
      id: '2',
      variable_name: 'POSITION',
      suggested_text: 'Software Developer',
      reason: 'Job title detected',
      position: { page: 1, line: 10 },
      status: 'pending'
    },
    {
      id: '3',
      variable_name: 'ANSPRECHPARTNER',
      suggested_text: 'Herr Mueller',
      reason: 'Contact person detected',
      position: { page: 1, line: 15 },
      status: 'accepted'
    }
  ]

  describe('rendering', () => {
    it('renders suggestion cards for each suggestion', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      const cards = wrapper.findAll('.suggestion-card')
      expect(cards).toHaveLength(3)
    })

    it('displays correct stats summary', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      expect(wrapper.find('.stats-summary').text()).toContain('3') // total
      expect(wrapper.text()).toContain('Erkannte Variablen')
    })

    it('shows empty state when no suggestions', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: [] }
      })

      expect(wrapper.find('.empty-state').exists()).toBe(true)
      expect(wrapper.text()).toContain('Keine Variablen erkannt')
    })

    it('displays variable name and suggested text', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      expect(wrapper.text()).toContain('FIRMA')
      expect(wrapper.text()).toContain('Muster GmbH')
    })

    it('displays reason when provided', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      expect(wrapper.text()).toContain('Company name detected')
    })

    it('displays position information', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      expect(wrapper.text()).toContain('Seite 1')
    })
  })

  describe('accept/reject actions', () => {
    it('emits accept event when accept button clicked', async () => {
      const suggestions = createSuggestions()
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      // Find first pending suggestion's accept button
      const acceptBtn = wrapper.find('.suggestion-card.is-pending .accept-btn')
      await acceptBtn.trigger('click')

      expect(wrapper.emitted('accept')).toBeTruthy()
      expect(wrapper.emitted('accept')[0][0]).toEqual(suggestions[0])
    })

    it('emits reject event when reject button clicked', async () => {
      const suggestions = createSuggestions()
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      const rejectBtn = wrapper.find('.suggestion-card.is-pending .reject-btn')
      await rejectBtn.trigger('click')

      expect(wrapper.emitted('reject')).toBeTruthy()
      expect(wrapper.emitted('reject')[0][0]).toEqual(suggestions[0])
    })

    it('shows status badge for accepted suggestions', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      const acceptedCard = wrapper.find('.suggestion-card.is-accepted')
      expect(acceptedCard.exists()).toBe(true)
      expect(acceptedCard.find('.status-badge.accepted').exists()).toBe(true)
      expect(acceptedCard.text()).toContain('Angenommen')
    })

    it('shows undo button for decided suggestions', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      const acceptedCard = wrapper.find('.suggestion-card.is-accepted')
      expect(acceptedCard.find('.undo-btn').exists()).toBe(true)
    })
  })

  describe('bulk actions', () => {
    it('shows bulk action buttons when pending items exist', () => {
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions: createSuggestions() }
      })

      expect(wrapper.find('.bulk-actions').exists()).toBe(true)
      expect(wrapper.text()).toContain('Alle annehmen')
      expect(wrapper.text()).toContain('Alle ablehnen')
    })

    it('hides bulk actions when no pending items', () => {
      const suggestions = createSuggestions().map(s => ({
        ...s,
        status: 'accepted'
      }))

      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      expect(wrapper.find('.bulk-actions').exists()).toBe(false)
    })

    it('emits accept for all pending when "accept all" clicked', async () => {
      const suggestions = createSuggestions()
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      const acceptAllBtn = wrapper.find('.bulk-actions button:first-child')
      await acceptAllBtn.trigger('click')

      // Should emit accept for each pending suggestion
      const emittedAccepts = wrapper.emitted('accept')
      expect(emittedAccepts).toBeTruthy()
      // 2 pending items in our test data
      expect(emittedAccepts.length).toBe(2)
    })

    it('emits reject for all pending when "reject all" clicked', async () => {
      const suggestions = createSuggestions()
      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      const rejectAllBtn = wrapper.find('.bulk-actions button:last-child')
      await rejectAllBtn.trigger('click')

      const emittedRejects = wrapper.emitted('reject')
      expect(emittedRejects).toBeTruthy()
      expect(emittedRejects.length).toBe(2)
    })
  })

  describe('computed counts', () => {
    it('correctly counts accepted suggestions', () => {
      const suggestions = [
        { id: '1', variable_name: 'FIRMA', suggested_text: 'Test', status: 'accepted' },
        { id: '2', variable_name: 'POSITION', suggested_text: 'Test', status: 'accepted' },
        { id: '3', variable_name: 'QUELLE', suggested_text: 'Test', status: 'pending' }
      ]

      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      const statAccepted = wrapper.find('.stat-accepted .stat-value')
      expect(statAccepted.text()).toBe('2')
    })

    it('correctly counts rejected suggestions', () => {
      const suggestions = [
        { id: '1', variable_name: 'FIRMA', suggested_text: 'Test', status: 'rejected' },
        { id: '2', variable_name: 'POSITION', suggested_text: 'Test', status: 'pending' }
      ]

      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      const statRejected = wrapper.find('.stat-rejected .stat-value')
      expect(statRejected.text()).toBe('1')
    })

    it('correctly counts pending suggestions', () => {
      const suggestions = [
        { id: '1', variable_name: 'FIRMA', suggested_text: 'Test', status: 'pending' },
        { id: '2', variable_name: 'POSITION', suggested_text: 'Test' }, // no status = pending
        { id: '3', variable_name: 'QUELLE', suggested_text: 'Test', status: 'accepted' }
      ]

      const wrapper = mount(VariableReviewStep, {
        props: { suggestions }
      })

      const statPending = wrapper.find('.stat-pending .stat-value')
      expect(statPending.text()).toBe('2')
    })
  })

  describe('variable styling', () => {
    it('applies correct CSS class for FIRMA variable', () => {
      const wrapper = mount(VariableReviewStep, {
        props: {
          suggestions: [
            { id: '1', variable_name: 'FIRMA', suggested_text: 'Test', status: 'pending' }
          ]
        }
      })

      expect(wrapper.find('.variable-badge.var-firma').exists()).toBe(true)
    })

    it('applies correct CSS class for POSITION variable', () => {
      const wrapper = mount(VariableReviewStep, {
        props: {
          suggestions: [
            { id: '1', variable_name: 'POSITION', suggested_text: 'Test', status: 'pending' }
          ]
        }
      })

      expect(wrapper.find('.variable-badge.var-position').exists()).toBe(true)
    })
  })
})
