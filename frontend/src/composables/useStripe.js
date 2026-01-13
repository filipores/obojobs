/**
 * Stripe Composable
 *
 * Initializes and provides access to the Stripe.js library.
 * Uses the publishable key from environment variables.
 */

import { ref, readonly } from 'vue'
import { loadStripe } from '@stripe/stripe-js'

// Singleton Stripe instance
let stripePromise = null
const stripeInstance = ref(null)
const isLoading = ref(false)
const error = ref(null)

/**
 * Get or initialize the Stripe instance
 * @returns {Promise<Stripe>} The Stripe instance
 */
async function getStripe() {
  // Return existing instance if available
  if (stripeInstance.value) {
    return stripeInstance.value
  }

  // Return pending promise if already loading
  if (stripePromise) {
    return stripePromise
  }

  const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

  if (!publishableKey) {
    const err = new Error('VITE_STRIPE_PUBLISHABLE_KEY is not configured')
    error.value = err.message
    throw err
  }

  isLoading.value = true
  error.value = null

  try {
    stripePromise = loadStripe(publishableKey)
    stripeInstance.value = await stripePromise
    return stripeInstance.value
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

/**
 * Redirect to Stripe Checkout
 * @param {string} sessionId - The Checkout Session ID from the backend
 */
async function redirectToCheckout(sessionId) {
  const stripe = await getStripe()
  const result = await stripe.redirectToCheckout({ sessionId })

  if (result.error) {
    error.value = result.error.message
    throw new Error(result.error.message)
  }
}

/**
 * Composable for Stripe operations
 */
export function useStripe() {
  return {
    stripe: readonly(stripeInstance),
    isLoading: readonly(isLoading),
    error: readonly(error),
    getStripe,
    redirectToCheckout,
  }
}

export default useStripe
