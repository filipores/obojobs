/* global IntersectionObserver */
import { onMounted, onUnmounted } from 'vue'

export function useScrollReveal() {
  let observer = null

  function observeElements() {
    const elements = document.querySelectorAll('[data-reveal]:not(.revealed)')
    elements.forEach((el) => observer.observe(el))
  }

  onMounted(() => {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed')
            observer.unobserve(entry.target)
          }
        })
      },
      {
        root: null,
        rootMargin: '0px 0px -60px 0px',
        threshold: 0.1
      }
    )

    window.requestAnimationFrame(() => {
      observeElements()
    })
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  })
}
