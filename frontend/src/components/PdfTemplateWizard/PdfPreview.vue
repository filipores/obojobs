<template>
  <div class="pdf-preview">
    <div class="preview-header">
      <h4>PDF-Vorschau</h4>
      <div class="preview-controls">
        <button
          class="control-btn"
          :disabled="currentPage <= 1"
          @click="prevPage"
          title="Vorherige Seite"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <span class="page-indicator">{{ currentPage }} / {{ totalPages }}</span>
        <button
          class="control-btn"
          :disabled="currentPage >= totalPages"
          @click="nextPage"
          :title="t('components.pdfPreview.nextPage')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
        <div class="control-divider"></div>
        <button
          class="control-btn"
          @click="zoomOut"
          :disabled="scale <= 0.5"
          title="Verkleinern"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            <line x1="8" y1="11" x2="14" y2="11"/>
          </svg>
        </button>
        <span class="zoom-indicator">{{ Math.round(scale * 100) }}%</span>
        <button
          class="control-btn"
          @click="zoomIn"
          :disabled="scale >= 2"
          :title="t('components.pdfPreview.zoomIn')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            <line x1="11" y1="8" x2="11" y2="14"/>
            <line x1="8" y1="11" x2="14" y2="11"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="preview-container" ref="containerRef">
      <!-- Loading State -->
      <div v-if="loading" class="preview-loading">
        <div class="loading-spinner"></div>
        <span>PDF wird geladen...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="preview-error">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <h4>PDF konnte nicht geladen werden</h4>
        <p>{{ error }}</p>
      </div>

      <!-- PDF Canvas -->
      <div v-else class="canvas-wrapper" :style="{ transform: `scale(${scale})` }">
        <canvas ref="canvasRef" class="pdf-canvas"></canvas>

        <!-- Highlight Overlays -->
        <div class="highlights-layer">
          <div
            v-for="(highlight, index) in currentPageHighlights"
            :key="index"
            class="highlight-box"
            :class="getHighlightClass(highlight)"
            :style="getHighlightStyle(highlight)"
            :title="highlight.variable_name"
          >
            <span class="highlight-label">{{ highlight.variable_name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Highlight Legend -->
    <div v-if="highlights.length > 0" class="highlight-legend">
      <span class="legend-title">Erkannte Variablen:</span>
      <div class="legend-items">
        <span
          v-for="type in uniqueVariableTypes"
          :key="type"
          class="legend-item"
          :class="getHighlightClass({ variable_name: type })"
        >
          {{ type }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, watch, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as pdfjsLib from 'pdfjs-dist'

const { t } = useI18n()

// Set worker source
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).href

const props = defineProps({
  pdfUrl: {
    type: String,
    default: ''
  },
  pdfFile: {
    type: File,
    default: null
  },
  highlights: {
    type: Array,
    default: () => []
  }
})

const containerRef = ref(null)
const canvasRef = ref(null)
const loading = ref(false)
const error = ref('')
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(0.75)  // Default to 75% zoom for better fit
const pageWidth = ref(0)
const pageHeight = ref(0)

// shallowRef prevents Vue's Proxy wrapping which breaks pdf.js private fields
const pdfDoc = shallowRef(null)

// Tracks current load operation to prevent race conditions
let loadId = 0

const HIGHLIGHT_CLASS_MAP = {
  FIRMA: 'hl-firma',
  POSITION: 'hl-position',
  ANSPRECHPARTNER: 'hl-ansprechpartner',
  QUELLE: 'hl-quelle',
  EINLEITUNG: 'hl-einleitung',
  DATUM: 'hl-datum',
  NAME: 'hl-name',
  ADRESSE: 'hl-adresse'
}

const currentPageHighlights = computed(() => {
  return props.highlights.filter(h => {
    const page = h.position?.page || h.page || 1
    return page === currentPage.value
  })
})

const uniqueVariableTypes = computed(() => {
  return [...new Set(props.highlights.map(h => h.variable_name))]
})

watch([() => props.pdfUrl, () => props.pdfFile], loadPdf, { immediate: true })

watch([currentPage, scale], async () => {
  if (pdfDoc.value && !loading.value) {
    await renderPage()
  }
})

onUnmounted(() => {
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
    pdfDoc.value = null
  }
})

async function loadPdf() {
  if (!props.pdfUrl && !props.pdfFile) {
    return
  }

  const currentLoadId = ++loadId
  loading.value = true
  error.value = ''

  function isStale() {
    return currentLoadId !== loadId
  }

  try {
    let loadingTask

    if (props.pdfFile) {
      const arrayBuffer = await props.pdfFile.arrayBuffer()
      if (isStale()) return
      loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    } else {
      loadingTask = pdfjsLib.getDocument(props.pdfUrl)
    }

    const newDoc = await loadingTask.promise
    if (isStale()) {
      newDoc.destroy()
      return
    }

    pdfDoc.value = newDoc
    totalPages.value = newDoc.numPages
    currentPage.value = 1
    loading.value = false

    await nextTick()
    if (isStale()) return
    await renderPage()
  } catch (err) {
    if (isStale()) return
    console.error('Error loading PDF:', err)
    error.value = err.message || 'Unbekannter Fehler beim Laden des PDF'
    loading.value = false
  }
}

async function renderPage() {
  const currentDoc = pdfDoc.value
  if (!currentDoc || !canvasRef.value) return

  function isStale() {
    return pdfDoc.value !== currentDoc
  }

  try {
    const page = await currentDoc.getPage(currentPage.value)
    if (isStale()) return

    const viewport = page.getViewport({ scale: 1.5 })
    const canvas = canvasRef.value
    if (!canvas) return

    canvas.height = viewport.height
    canvas.width = viewport.width
    pageWidth.value = viewport.width
    pageHeight.value = viewport.height

    if (isStale()) return

    await page.render({
      canvasContext: canvas.getContext('2d'),
      viewport
    }).promise
  } catch (err) {
    // Ignore private field errors from pdf.js race conditions during document switching
    const isPrivateFieldError = err?.message?.includes('private field')
    if (!isStale() && !isPrivateFieldError) {
      console.error('Error rendering page:', err)
      error.value = 'Fehler beim Rendern der Seite'
    }
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

function zoomIn() {
  scale.value = Math.min(2, scale.value + 0.25)
}

function zoomOut() {
  scale.value = Math.max(0.5, scale.value - 0.25)
}

function getHighlightClass(highlight) {
  const name = highlight.variable_name?.toUpperCase() || ''
  return HIGHLIGHT_CLASS_MAP[name] || 'hl-default'
}

// PDF render scale (must match the scale used in renderPage)
const PDF_RENDER_SCALE = 1.5

function getHighlightStyle(highlight) {
  const pos = highlight.position || {}
  // Backend sends absolute PDF coordinates (in points)
  // Multiply by render scale to convert to canvas pixels
  const x = (pos.x || 0) * PDF_RENDER_SCALE
  const y = (pos.y || 0) * PDF_RENDER_SCALE
  const width = (pos.width || 50) * PDF_RENDER_SCALE
  const height = (pos.height || 15) * PDF_RENDER_SCALE

  return {
    left: `${x}px`,
    top: `${y}px`,
    width: `${width}px`,
    height: `${height}px`
  }
}
</script>

<style scoped>
.pdf-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-washi, #FAF8F3);
  border-radius: var(--radius-md, 0.5rem);
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md, 1rem);
  background: var(--color-washi-warm, #F2EDE3);
  border-bottom: 1px solid var(--color-border-light, #E5DFD4);
}

.preview-header h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-sumi, #2C2C2C);
  margin: 0;
}

.preview-controls {
  display: flex;
  align-items: center;
  gap: var(--space-xs, 0.25rem);
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: var(--color-washi-cream, #FAF8F3);
  border: 1px solid var(--color-border, #D4C9BA);
  border-radius: var(--radius-sm, 0.25rem);
  color: var(--color-text-secondary, #4A4A4A);
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
}

.control-btn:hover:not(:disabled) {
  background: var(--color-washi-aged, #E8E2D5);
  border-color: var(--color-stone, #9B958F);
}

.control-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-indicator,
.zoom-indicator {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary, #6B6B6B);
  min-width: 60px;
  text-align: center;
}

.control-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border, #D4C9BA);
  margin: 0 var(--space-xs, 0.25rem);
}

/* Preview Container */
.preview-container {
  flex: 1;
  overflow: auto;
  padding: var(--space-md, 1rem);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: var(--color-stone, #9B958F);
}

.canvas-wrapper {
  position: relative;
  transform-origin: top center;
  transition: transform 200ms ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.pdf-canvas {
  display: block;
  background: white;
}

/* Loading State */
.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md, 1rem);
  padding: var(--space-xl, 2rem);
  color: var(--color-washi, #FAF8F3);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--color-washi, #FAF8F3);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl, 2rem);
  text-align: center;
  color: var(--color-washi, #FAF8F3);
}

.preview-error svg {
  margin-bottom: var(--space-md, 1rem);
  opacity: 0.7;
}

.preview-error h4 {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: var(--space-sm, 0.5rem);
}

.preview-error p {
  font-size: 0.875rem;
  opacity: 0.8;
}

/* Highlights Layer */
.highlights-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.highlight-box {
  position: absolute;
  border: 2px solid;
  border-radius: 2px;
  pointer-events: auto;
  cursor: pointer;
  transition: all var(--transition-subtle, 200ms ease);
}

.highlight-box:hover {
  transform: scale(1.02);
  z-index: 10;
}

.highlight-label {
  position: absolute;
  top: -20px;
  left: 0;
  padding: 2px 6px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  border-radius: 2px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 200ms ease;
}

.highlight-box:hover .highlight-label {
  opacity: 1;
}

/* Highlight Colors */
.hl-firma {
  border-color: var(--color-ai, #3D5A6C);
  background: rgba(61, 90, 108, 0.2);
}
.hl-firma .highlight-label {
  background: var(--color-ai, #3D5A6C);
  color: white;
}

.hl-position {
  border-color: var(--color-success, #7A8B6E);
  background: rgba(122, 139, 110, 0.2);
}
.hl-position .highlight-label {
  background: var(--color-success, #7A8B6E);
  color: white;
}

.hl-ansprechpartner {
  border-color: var(--color-warning, #C4A35A);
  background: rgba(196, 163, 90, 0.2);
}
.hl-ansprechpartner .highlight-label {
  background: var(--color-warning, #C4A35A);
  color: white;
}

.hl-quelle {
  border-color: var(--color-terra, #B87A5E);
  background: rgba(184, 122, 94, 0.2);
}
.hl-quelle .highlight-label {
  background: var(--color-terra, #B87A5E);
  color: white;
}

.hl-einleitung {
  border-color: var(--color-bamboo, #8B9A6B);
  background: rgba(139, 154, 107, 0.2);
}
.hl-einleitung .highlight-label {
  background: var(--color-bamboo, #8B9A6B);
  color: white;
}

.hl-datum,
.hl-name,
.hl-adresse,
.hl-default {
  border-color: var(--color-stone, #9B958F);
  background: rgba(155, 149, 143, 0.2);
}
.hl-default .highlight-label {
  background: var(--color-stone, #9B958F);
  color: white;
}

/* Highlight Legend */
.highlight-legend {
  padding: var(--space-md, 1rem);
  background: var(--color-washi-warm, #F2EDE3);
  border-top: 1px solid var(--color-border-light, #E5DFD4);
}

.legend-title {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-tertiary, #6B6B6B);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  margin-bottom: var(--space-sm, 0.5rem);
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm, 0.5rem);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  padding: var(--space-xs, 0.25rem) var(--space-sm, 0.5rem);
  border-radius: var(--radius-sm, 0.25rem);
  font-size: 0.75rem;
  font-weight: 500;
}

.legend-item.hl-firma {
  background: var(--color-ai-subtle, rgba(61, 90, 108, 0.12));
  color: var(--color-ai, #3D5A6C);
}

.legend-item.hl-position {
  background: var(--color-success-light, rgba(122, 139, 110, 0.15));
  color: var(--color-success, #7A8B6E);
}

.legend-item.hl-ansprechpartner {
  background: var(--color-warning-light, rgba(196, 163, 90, 0.15));
  color: var(--color-warning, #C4A35A);
}

.legend-item.hl-quelle {
  background: rgba(184, 122, 94, 0.12);
  color: var(--color-terra, #B87A5E);
}

.legend-item.hl-einleitung {
  background: rgba(139, 154, 107, 0.12);
  color: var(--color-bamboo, #8B9A6B);
}

.legend-item.hl-default {
  background: var(--color-washi-aged, #E8E2D5);
  color: var(--color-stone, #9B958F);
}
</style>
