/**
 * Subscription Composable
 *
 * Handles subscription-related operations including
 * plan fetching, checkout creation, and status management.
 */

import { ref, readonly } from 'vue'
import api from '../api/client'
import { useStripe } from './useStripe'

const plans = ref([])
const paymentsAvailable = ref(true)
const isLoading = ref(false)
const error = ref(null)

/**
 * Fetch available subscription plans
 * @returns {Promise<Array>} List of subscription plans
 */
async function fetchPlans() {
  isLoading.value = true
  error.value = null

  try {
    const { data } = await api.get('/subscriptions/plans')
    if (data.success) {
      plans.value = data.data
      if (data.payments_available !== undefined) {
        paymentsAvailable.value = data.payments_available
      }
      return data.data
    }
    throw new Error('Failed to fetch plans')
  } catch (err) {
    error.value = err.response?.data?.error || err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

/**
 * Create a checkout session and redirect to Stripe Checkout
 * @param {string} plan - Plan ID ('basic' or 'pro')
 * @returns {Promise<void>}
 */
async function startCheckout(plan) {
  if (!['basic', 'pro'].includes(plan)) {
    throw new Error('Invalid plan. Must be "basic" or "pro"')
  }

  isLoading.value = true
  error.value = null

  try {
    const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`
    const cancelUrl = `${window.location.origin}/buy-credits`

    const { data } = await api.post('/subscriptions/create-checkout', {
      plan,
      success_url: successUrl,
      cancel_url: cancelUrl
    })

    if (data.success && data.data.session_id) {
      // Redirect to Stripe Checkout
      const { redirectToCheckout } = useStripe()
      await redirectToCheckout(data.data.session_id)
    } else {
      throw new Error(data.error || 'Failed to create checkout session')
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

/**
 * Fetch current user's subscription details
 * @returns {Promise<Object>} Current subscription data
 */
async function fetchCurrentSubscription() {
  isLoading.value = true
  error.value = null

  try {
    const { data } = await api.get('/subscriptions/current')
    if (data.success) {
      if (data.data.payments_available !== undefined) {
        paymentsAvailable.value = data.data.payments_available
      }
      return data.data
    }
    throw new Error('Failed to fetch subscription')
  } catch (err) {
    error.value = err.response?.data?.error || err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

/**
 * Open Stripe Customer Portal for subscription management
 * @returns {Promise<void>}
 */
async function openBillingPortal() {
  isLoading.value = true
  error.value = null

  try {
    const returnUrl = `${window.location.origin}/settings`

    const { data } = await api.post('/subscriptions/portal', {
      return_url: returnUrl
    })

    if (data.success && data.data.portal_url) {
      // Redirect to Stripe Portal
      window.location.href = data.data.portal_url
    } else {
      throw new Error(data.error || 'Failed to open billing portal')
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

/**
 * Composable for subscription operations
 */
export function useSubscription() {
  return {
    plans: readonly(plans),
    paymentsAvailable: readonly(paymentsAvailable),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetchPlans,
    startCheckout,
    fetchCurrentSubscription,
    openBillingPortal
  }
}

export default useSubscription
