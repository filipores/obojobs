/**
 * Subscription Composable
 *
 * Handles credit-based plan operations including
 * plan fetching, checkout creation, and status management.
 */

import { ref, readonly } from 'vue'
import api from '../api/client'

const PAID_PLANS = ['starter', 'pro']

const plans = ref([])
const paymentsAvailable = ref(true)
const isLoading = ref(false)
const error = ref(null)

function extractErrorMessage(err) {
  return err.response?.data?.error || err.message
}

function validatePaidPlan(plan) {
  if (!PAID_PLANS.includes(plan)) {
    throw new Error('Invalid plan. Must be "starter" or "pro"')
  }
}

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
    error.value = extractErrorMessage(err)
    throw err
  } finally {
    isLoading.value = false
  }
}

async function startCheckout(plan) {
  validatePaidPlan(plan)
  isLoading.value = true
  error.value = null

  try {
    const successUrl = `${window.location.origin}/subscription/success?session_id={CHECKOUT_SESSION_ID}`
    const cancelUrl = `${window.location.origin}/subscription`

    const { data } = await api.post('/subscriptions/create-checkout', {
      plan,
      success_url: successUrl,
      cancel_url: cancelUrl
    })

    if (data.success && data.data.checkout_url) {
      window.location.href = data.data.checkout_url
    } else {
      throw new Error(data.error || 'Failed to create checkout session')
    }
  } catch (err) {
    error.value = extractErrorMessage(err)
    throw err
  } finally {
    isLoading.value = false
  }
}

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
    error.value = extractErrorMessage(err)
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
    fetchCurrentSubscription
  }
}

export default useSubscription
