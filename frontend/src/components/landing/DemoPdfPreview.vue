<template>
  <div class="demo-pdf-preview zen-card" :class="{ 'floating-mode': floating }">
    <div class="pdf-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
      <span>Dein Anschreiben</span>
    </div>
    <div class="pdf-canvas-wrapper">
      <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
      <div class="pdf-fade-overlay"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, watch, onUnmounted } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

// Set worker source
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).href

const props = defineProps({
  pdfBlob: {
    type: Object,
    required: false,
    default: null
  },
  floating: {
    type: Boolean,
    default: false
  }
})

const pdfCanvas = ref(null)
const pdfDoc = shallowRef(null)

// Tracks current load operation to prevent race conditions
let loadId = 0
let currentBlobUrl = null

watch(() => props.pdfBlob, renderPdf, { immediate: true })

onUnmounted(() => {
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
    pdfDoc.value = null
  }
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl)
    currentBlobUrl = null
  }
})

async function renderPdf() {
  if (!props.pdfBlob) {
    return
  }

  const currentLoadId = ++loadId

  function isStale() {
    return currentLoadId !== loadId
  }

  // Clean up previous blob URL
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl)
    currentBlobUrl = null
  }

  // Clean up previous document
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
    pdfDoc.value = null
  }

  try {
    // Create blob URL from the blob
    currentBlobUrl = URL.createObjectURL(props.pdfBlob)

    const loadingTask = pdfjsLib.getDocument(currentBlobUrl)
    const newDoc = await loadingTask.promise

    if (isStale()) {
      newDoc.destroy()
      return
    }

    pdfDoc.value = newDoc

    // Get and render first page
    const page = await newDoc.getPage(1)
    if (isStale()) return

    const viewport = page.getViewport({ scale: 0.5 })
    const canvas = pdfCanvas.value
    if (!canvas) return

    canvas.height = viewport.height
    canvas.width = viewport.width

    if (isStale()) return

    await page.render({
      canvasContext: canvas.getContext('2d'),
      viewport
    }).promise
  } catch (err) {
    // Ignore private field errors from pdf.js race conditions during document switching
    const isPrivateFieldError = err?.message?.includes('private field')
    if (!isStale() && !isPrivateFieldError) {
      console.error('Error rendering PDF preview:', err)
    }
  }
}
</script>

<style scoped>
.demo-pdf-preview {
  max-width: 280px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lifted);
}

/* Floating mode for hover preview */
.demo-pdf-preview.floating-mode {
  box-shadow: var(--shadow-modal);
  animation: pdfPreviewScaleIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes pdfPreviewScaleIn {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(8px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.pdf-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-washi-warm);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--color-text-ghost);
}

.pdf-canvas-wrapper {
  position: relative;
  max-height: 320px;
  overflow: hidden;
}

.pdf-canvas {
  width: 100%;
  display: block;
}

.pdf-fade-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: linear-gradient(to bottom, transparent, var(--color-bg-elevated));
  pointer-events: none;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .demo-pdf-preview.floating-mode {
    animation: none;
    opacity: 1;
  }
}
</style>
