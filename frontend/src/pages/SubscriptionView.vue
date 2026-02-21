<template>
  <div class="subscription-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <h1>{{ t('subscription.pageTitle') }}</h1>
        <p class="page-subtitle">{{ t('subscription.pageSubtitle') }}</p>
      </section>

      <!-- Loading State -->
      <div v-if="isLoading && !subscription" class="loading-state">
        <div class="loading-spinner"></div>
        <p>{{ t('subscription.loadingDetails') }}</p>
      </div>

      <!-- Content (visible after loading) -->
      <template v-else>

      <!-- Payment Failed Banner -->
      <div v-if="subscription?.status === 'past_due'" class="payment-failed-banner animate-fade-up" style="animation-delay: 75ms;">
        <div class="banner-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <div class="banner-content">
          <strong>{{ t('subscription.paymentFailedTitle') }}</strong>
          <p>{{ t('subscription.paymentFailedMessage') }}</p>
        </div>
        <button @click="handleOpenPortal" class="zen-btn zen-btn-filled banner-action" :disabled="isPortalLoading">
          {{ isPortalLoading ? t('common.loading') : t('subscription.updatePaymentMethod') }}
        </button>
      </div>

      <!-- Current Plan Section -->
      <section class="subscription-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20 12V8H6a2 2 0 0 1-2-2c0-1.1.9-2 2-2h12v4"/>
              <path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/>
              <path d="M18 12a2 2 0 0 0-2 2c0 1.1.9 2 2 2h4v-4h-4z"/>
            </svg>
          </div>
          <h2>{{ t('subscription.currentPlan') }}</h2>
        </div>

        <div class="settings-card zen-card current-plan-card">
          <div class="plan-header">
            <div class="plan-badge" :class="subscription?.plan">
              {{ getPlanDisplayName(subscription?.plan) }}
            </div>
            <span v-if="subscription?.status === 'active'" class="status-badge active">{{ t('subscription.active') }}</span>
            <span v-else-if="subscription?.status === 'canceled'" class="status-badge canceled">{{ t('subscription.statusCanceled') }}</span>
            <span v-else-if="subscription?.status === 'past_due'" class="status-badge past-due">{{ t('subscription.statusPastDue') }}</span>
            <span v-else-if="subscription?.status === 'trialing'" class="status-badge trialing">{{ t('subscription.statusTrialing') }}</span>
          </div>

          <div class="plan-details">
            <div class="detail-row">
              <span class="detail-label">{{ t('subscription.monthlyPrice') }}</span>
              <span class="detail-value">
                {{ subscription?.plan_details?.price_formatted || t('subscription.freePriceFormatted') }}
                <span v-if="subscription?.plan !== 'free'" class="mwst-hint">{{ t('subscription.includingVat') }}</span>
              </span>
            </div>
            <div class="detail-divider"></div>
            <div class="detail-row">
              <span class="detail-label">{{ t('subscription.nextBilling') }}</span>
              <span class="detail-value">{{ formatDate(subscription?.next_billing_date) || t('subscription.none') }}</span>
            </div>
          </div>

          <div class="plan-features">
            <h4>{{ t('subscription.includedFeatures') }}</h4>
            <ul class="features-list">
              <li v-for="feature in getCurrentPlanFeatures" :key="feature">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ feature }}
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Cancellation Pending Banner -->
      <div v-if="subscription?.cancel_at_period_end" class="cancellation-banner animate-fade-up" style="animation-delay: 125ms;">
        <div class="banner-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div class="banner-text">
          <strong>{{ t('subscription.cancellationPending') }}</strong>
          <p>{{ t('subscription.cancellationPendingDescription', { date: formatDate(subscription?.next_billing_date) }) }}</p>
        </div>
      </div>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Usage Section -->
      <section v-if="subscription" class="subscription-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <h2>{{ t('subscription.usageThisMonth') }}</h2>
        </div>

        <div class="settings-card zen-card usage-card">
          <div class="usage-display">
            <div class="usage-number">
              <span class="usage-current">{{ subscription.usage?.used || 0 }}</span>
              <span class="usage-separator">/</span>
              <span class="usage-limit">{{ subscription.usage?.unlimited ? t('subscription.unlimited') : subscription.usage?.limit }}</span>
            </div>
            <span class="usage-label">{{ t('subscription.applicationsCreated') }}</span>
          </div>

          <!-- Progress Bar (only for limited plans) -->
          <div v-if="!subscription.usage?.unlimited" class="usage-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: usagePercentage + '%' }"></div>
            </div>
            <div class="progress-info">
              <span>{{ subscription.usage?.remaining || 0 }} {{ t('subscription.remaining') }}</span>
              <span>{{ usagePercentage }}% {{ t('subscription.used') }}</span>
            </div>
          </div>

          <!-- Unlimited Badge -->
          <div v-else class="unlimited-badge">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18.178 8c5.096 0 5.096 8 0 8-5.095 0-7.133-8-12.739-8-4.585 0-4.585 8 0 8 5.606 0 7.644-8 12.74-8z"/>
            </svg>
            <span>{{ t('subscription.unlimitedApplications') }}</span>
          </div>
        </div>
      </section>

      <!-- Payments Unavailable Banner -->
      <div v-if="subscription && !paymentsAvailable" class="payments-unavailable-banner animate-fade-up" style="animation-delay: 175ms;">
        <div class="banner-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <div class="banner-text">
          <strong>{{ t('subscription.paymentsUnavailable') }}</strong>
          <p>{{ t('subscription.paymentsUnavailableDescription') }}</p>
        </div>
      </div>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Manage Subscription Section -->
      <section v-if="subscription" class="subscription-section animate-fade-up" style="animation-delay: 200ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
          <div>
            <h2>{{ t('subscription.manageSubscription') }}</h2>
            <p class="section-description">{{ t('subscription.manageDescription') }}</p>
          </div>
        </div>

        <div class="settings-card zen-card manage-card">
          <!-- Portal Access -->
          <div v-if="subscription.has_stripe_customer" class="portal-section">
            <p class="portal-info">
              {{ t('subscription.stripePortalInfo') }}
            </p>
            <button
              @click="handleOpenPortal"
              class="zen-btn zen-btn-filled"
              :disabled="isPortalLoading"
            >
              {{ isPortalLoading ? t('subscription.opening') : t('subscription.manageSubscription') }}
            </button>
          </div>

          <!-- Upgrade Prompt (for free users) -->
          <div v-else class="upgrade-section">
            <p class="upgrade-info">
              {{ paymentsAvailable
                ? t('subscription.currentFreePlan')
                : t('subscription.paymentsUnavailableDescription')
              }}
            </p>
            <div class="upgrade-buttons">
              <button
                @click="handleUpgrade('starter')"
                class="zen-btn zen-btn-filled"
                :class="{ 'is-loading-other': isUpgrading && upgradingPlan !== 'starter' }"
                :disabled="isUpgrading || !paymentsAvailable"
              >
                <span v-if="upgradingPlan === 'starter'" class="btn-spinner"></span>
                {{ upgradingPlan === 'starter' ? t('common.loading') : `Starter - 9,90 ${t('subscription.perMonth')} ${t('subscription.includingVatShort')}` }}
              </button>
              <button
                @click="handleUpgrade('pro')"
                class="zen-btn zen-btn-ai"
                :class="{ 'is-loading-other': isUpgrading && upgradingPlan !== 'pro' }"
                :disabled="isUpgrading || !paymentsAvailable"
              >
                <span v-if="upgradingPlan === 'pro'" class="btn-spinner"></span>
                {{ upgradingPlan === 'pro' ? t('common.loading') : `Pro - 19,90 ${t('subscription.perMonth')} ${t('subscription.includingVatShort')}` }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Plan Comparison Section - Always visible -->
      <section v-if="subscription" class="subscription-section animate-fade-up" style="animation-delay: 250ms;">
        <div class="section-header">
          <div class="section-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </div>
          <div>
            <h2>{{ t('subscription.allPlansComparison') }}</h2>
            <p class="section-description">{{ t('subscription.choosePlan') }}</p>
          </div>
        </div>

        <!-- Plan Comparison Table (Desktop) -->
        <div class="plan-comparison-table zen-card">
          <table class="comparison-table" role="grid" aria-label="Plan-Vergleichstabelle">
            <thead>
              <tr>
                <th class="feature-column">Features</th>
                <th
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  class="plan-column"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan, 'recommended-plan': plan.plan_id === 'pro' }"
                >
                  <div class="plan-header-cell">
                    <span v-if="plan.plan_id === subscription.plan" class="table-badge current">{{ t('subscription.badgeCurrent') }}</span>
                    <span v-else-if="plan.plan_id === 'pro'" class="table-badge recommended">{{ t('subscription.badgeRecommended') }}</span>
                    <span class="plan-name">{{ plan.name }}</span>
                    <span class="plan-price-cell">
                      {{ plan.price === 0 ? t('subscription.freeLabel') : plan.price.toFixed(2).replace('.', ',') + ' ' + t('subscription.perMonth') }}
                      <span v-if="plan.price > 0" class="mwst-hint">{{ t('subscription.includingVatShort') }}</span>
                    </span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="feature-name">{{ t('subscription.applicationsPerMonth') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span class="feature-value" :class="{ 'highlight': plan.plan_id === 'pro' }">
                    {{ getApplicationLimit(plan.plan_id) }}
                  </span>
                </td>
              </tr>
              <tr>
                <td class="feature-name">{{ t('subscription.aiGenerator') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">{{ t('subscription.templateManagement') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">{{ t('subscription.atsAnalysis') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">{{ t('subscription.emailSuggestions') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span v-if="plan.plan_id === 'free'" class="feature-limited">{{ t('subscription.emailSuggestionsLimited') }}</span>
                  <svg v-else class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">{{ t('subscription.salaryCoach') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span v-if="plan.plan_id === 'free'" class="feature-unavailable">—</span>
                  <svg v-else class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
              <tr>
                <td class="feature-name">{{ t('subscription.prioritySupport') }}</td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <span v-if="plan.plan_id !== 'pro'" class="feature-unavailable">—</span>
                  <svg v-else class="check-icon highlight" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td></td>
                <td
                  v-for="plan in getAvailablePlans"
                  :key="plan.plan_id"
                  :class="{ 'current-plan': plan.plan_id === subscription.plan }"
                >
                  <button
                    v-if="plan.plan_id !== subscription.plan && plan.plan_id !== 'free'"
                    @click="handleUpgrade(plan.plan_id)"
                    class="zen-btn upgrade-btn"
                    :class="[
                      plan.plan_id === 'pro' ? 'zen-btn-ai' : 'zen-btn-filled',
                      { 'is-loading-other': isUpgrading && upgradingPlan !== plan.plan_id }
                    ]"
                    :disabled="isUpgrading || !paymentsAvailable"
                  >
                    <span v-if="upgradingPlan === plan.plan_id" class="btn-spinner"></span>
                    {{ upgradingPlan === plan.plan_id ? t('common.loading') : getUpgradeButtonText(plan.plan_id) }}
                  </button>
                  <span v-else-if="plan.plan_id === subscription.plan" class="current-plan-indicator">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    {{ t('subscription.yourCurrentPlan') }}
                  </span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Plan Cards (Mobile) -->
        <div class="plans-grid mobile-only">
          <div
            v-for="plan in getAvailablePlans"
            :key="plan.plan_id"
            class="plan-card zen-card"
            :class="{ 'current': plan.plan_id === subscription.plan, 'recommended': plan.plan_id === 'pro' }"
          >
            <div v-if="plan.plan_id === 'pro' && plan.plan_id !== subscription.plan" class="recommended-badge">{{ t('subscription.badgeRecommended') }}</div>
            <div v-if="plan.plan_id === subscription.plan" class="current-badge">{{ t('subscription.currentPlan') }}</div>

            <h3>{{ plan.name }}</h3>
            <div class="plan-price">
              <span class="price-amount">{{ plan.price === 0 ? t('subscription.freeLabel') : plan.price.toFixed(2).replace('.', ',') + ' EUR' }}</span>
              <span v-if="plan.price > 0" class="price-period">/ {{ t('pricing.starter.period') }}</span>
              <span v-if="plan.price > 0" class="mwst-hint">{{ t('subscription.includingVatShort') }}</span>
            </div>

            <div class="plan-limit-badge">
              {{ getApplicationLimit(plan.plan_id) }} {{ t('subscription.applicationsPerMonthShort') }}
            </div>

            <ul class="plan-features-list">
              <li v-for="feature in plan.features" :key="feature">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {{ feature }}
              </li>
            </ul>

            <button
              v-if="plan.plan_id !== subscription.plan && plan.plan_id !== 'free'"
              @click="handleUpgrade(plan.plan_id)"
              class="zen-btn upgrade-btn-large"
              :class="[
                plan.plan_id === 'pro' ? 'zen-btn-ai' : 'zen-btn-filled',
                { 'is-loading-other': isUpgrading && upgradingPlan !== plan.plan_id }
              ]"
              :disabled="isUpgrading || !paymentsAvailable"
            >
              <span v-if="upgradingPlan === plan.plan_id" class="btn-spinner"></span>
              {{ upgradingPlan === plan.plan_id ? t('common.loading') : getUpgradeButtonText(plan.plan_id) }}
            </button>
            <div v-else-if="plan.plan_id === subscription.plan" class="current-plan-text">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              {{ t('subscription.yourCurrentPlan') }}
            </div>
          </div>
        </div>
      </section>

      <!-- Cancellation Section -->
      <section v-if="isPaidActive" class="subscription-section animate-fade-up" style="animation-delay: 275ms;">
        <div class="section-header">
          <div class="section-icon cancel-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <div>
            <h2>{{ t('subscription.cancelTitle') }}</h2>
            <p class="section-description">{{ t('subscription.cancelDescription') }}</p>
          </div>
        </div>

        <div class="settings-card zen-card cancel-card">
          <button @click="showCancelModal = true" class="zen-btn zen-btn-danger">
            {{ t('subscription.cancelButton') }}
          </button>
        </div>
      </section>

      <!-- Cancel Confirmation Modal -->
      <Teleport to="body">
        <div v-if="showCancelModal" class="modal-overlay" @click.self="showCancelModal = false">
          <div class="modal-content zen-card cancel-modal">
            <h3>{{ t('subscription.confirmCancelTitle') }}</h3>
            <p class="modal-description" v-html="t('subscription.confirmCancelMessage', { plan: getPlanDisplayName(subscription?.plan), date: formatDate(subscription?.next_billing_date) })">
            </p>
            <div class="modal-actions">
              <button @click="showCancelModal = false" class="zen-btn zen-btn-ghost" :disabled="isCanceling">
                {{ t('common.cancel') }}
              </button>
              <button @click="handleCancelSubscription" class="zen-btn zen-btn-danger" :disabled="isCanceling">
                <span v-if="isCanceling" class="btn-spinner"></span>
                {{ isCanceling ? t('subscription.canceling') : t('subscription.cancelNow') }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Error Message -->
      <div v-if="errorMessage" class="error-message animate-fade-up">
        {{ errorMessage }}
      </div>

      </template>
    </div>

    <!-- Plan Change Confirmation Modal -->
    <Teleport to="body">
      <div v-if="showConfirmation" class="modal-overlay" @click.self="cancelConfirmation">
        <div class="modal zen-card" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
          <div class="modal-header">
            <h3 id="confirm-title">{{ t('subscription.confirmChangeTitle') }}</h3>
            <button @click="cancelConfirmation" class="modal-close" :aria-label="t('common.close')">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Plan transition -->
            <div class="plan-transition">
              <div class="plan-transition-item">
                <span class="plan-transition-label">{{ t('subscription.currentPlanLabel') }}</span>
                <span class="plan-transition-name">{{ getPlanDisplayName(subscription?.plan) }}</span>
              </div>
              <div class="plan-transition-arrow">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                  <polyline points="12 5 19 12 12 19"/>
                </svg>
              </div>
              <div class="plan-transition-item">
                <span class="plan-transition-label">{{ t('subscription.newPlanLabel') }}</span>
                <span class="plan-transition-name highlight">{{ getPlanDisplayName(pendingPlanChange) }}</span>
              </div>
            </div>

            <!-- Proration details -->
            <div v-if="prorationPreview" class="proration-details">
              <div class="proration-row">
                <span class="proration-label">{{ t('subscription.immediateCharge') }}</span>
                <span class="proration-value">{{ formatEUR(prorationPreview.immediate_charge) }}</span>
              </div>
              <div class="proration-divider"></div>
              <div class="proration-row">
                <span class="proration-label">{{ t('subscription.nextBillingDate') }}</span>
                <span class="proration-value">{{ formatTimestamp(prorationPreview.next_billing_date) }}</span>
              </div>
              <div class="proration-row">
                <span class="proration-label">{{ t('subscription.newPrice') }}</span>
                <span class="proration-value">{{ prorationPreview.new_plan_price }}</span>
              </div>
            </div>

            <!-- Explanation -->
            <div class="proration-explanation">
              <p v-if="isUpgradeDirection(pendingPlanChange)">
                {{ t('subscription.upgradeExplanation') }}
              </p>
              <p v-else>
                {{ t('subscription.downgradeExplanation') }}
              </p>
            </div>
          </div>

          <div class="modal-actions">
            <button @click="cancelConfirmation" class="zen-btn zen-btn-ghost">
              {{ t('common.cancel') }}
            </button>
            <button
              @click="confirmPlanChange"
              class="zen-btn"
              :class="isUpgradeDirection(pendingPlanChange) ? 'zen-btn-ai' : 'zen-btn-filled'"
              :disabled="isUpgrading"
            >
              <span v-if="isUpgrading" class="btn-spinner"></span>
              {{ isUpgrading ? t('subscription.changingPlan') : t('subscription.confirmButton') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSubscription } from '../composables/useSubscription'
import { getFullLocale } from '../i18n'

const { t } = useI18n()
const { fetchPlans, fetchCurrentSubscription, startCheckout, isLoading, paymentsAvailable } = useSubscription()

// Stub functions for legacy subscription management (now credit-based)
const openBillingPortal = async () => { console.warn('Billing portal not available in credit-based model') }
const previewPlanChange = async () => ({ amount: 0 })
const changePlan = async () => { console.warn('Plan changes not available in credit-based model') }
const cancelSubscription = async () => { console.warn('Subscription cancellation not available in credit-based model') }

const subscription = ref(null)
const availablePlans = ref([])
const isPortalLoading = ref(false)
const isUpgrading = ref(false)
const upgradingPlan = ref(null)
const errorMessage = ref('')
const showConfirmation = ref(false)
const prorationPreview = ref(null)
const pendingPlanChange = ref(null)
const isPreviewLoading = ref(false)
const showCancelModal = ref(false)
const isCanceling = ref(false)

const PLAN_ORDER = { free: 0, starter: 1, pro: 2 }

const fallbackPlans = computed(() => [
  {
    plan_id: 'free',
    name: 'Free',
    price: 0,
    price_formatted: t('subscription.freePriceFormatted'),
    features: [
      `3 ${t('subscription.applicationsPerMonth')}`,
      t('subscription.basicTemplates'),
      t('subscription.pdfExport')
    ]
  },
  {
    plan_id: 'starter',
    name: 'Starter',
    price: 9.90,
    price_formatted: t('subscription.starterPriceFormatted'),
    features: [
      `50 ${t('subscription.applicationsPerMonth')}`,
      t('subscription.allTemplates'),
      t('subscription.pdfExport'),
      t('subscription.atsOptimization'),
      t('subscription.emailSupport')
    ]
  },
  {
    plan_id: 'pro',
    name: 'Pro',
    price: 19.90,
    price_formatted: t('subscription.proPriceFormatted'),
    features: [
      t('subscription.unlimitedApplications'),
      t('subscription.allTemplates'),
      t('subscription.pdfExport'),
      t('subscription.atsOptimization'),
      t('subscription.prioritySupport'),
      t('subscription.advancedAnalysis')
    ]
  }
])

const usagePercentage = computed(() => {
  if (!subscription.value?.usage || subscription.value.usage.unlimited) return 0
  const { used, limit } = subscription.value.usage
  if (limit === 0) return 0
  return Math.min(Math.round((used / limit) * 100), 100)
})

const getCurrentPlanFeatures = computed(() => {
  if (subscription.value?.plan_details?.features?.length) {
    return subscription.value.plan_details.features
  }

  // Fallback: look up from available plans (always has hardcoded defaults)
  const currentPlan = subscription.value?.plan || 'free'
  const match = getAvailablePlans.value.find(p => p.plan_id === currentPlan)
  return match?.features || []
})

const getAvailablePlans = computed(() => {
  return availablePlans.value?.length > 0 ? availablePlans.value : fallbackPlans.value
})

const getPlanDisplayName = (plan) => {
  const names = {
    free: t('subscription.free'),
    starter: t('subscription.starter'),
    pro: t('subscription.pro')
  }
  return names[plan] || t('subscription.free')
}

const formatDate = (dateString) => {
  if (!dateString) return null
  return new Date(dateString).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatTimestamp = (ts) => {
  if (!ts) return null
  return new Date(ts * 1000).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatEUR = (amount) => {
  if (amount == null || isNaN(amount)) return '0,00 EUR'
  return amount.toFixed(2).replace('.', ',') + ' EUR'
}

const getUpgradeButtonText = (planId) => {
  if (!subscription.value) return t('subscription.upgrade')
  const targetOrder = PLAN_ORDER[planId] || 0
  const currentOrder = PLAN_ORDER[subscription.value.plan] || 0

  if (targetOrder > currentOrder) return t('subscription.upgrade')
  if (targetOrder < currentOrder) return t('subscription.downgrade')
  return t('subscription.currentPlan')
}

const getApplicationLimit = (planId) => {
  const limits = {
    free: '3',
    starter: '50',
    pro: t('subscription.unlimited')
  }
  return limits[planId] || '3'
}

const handleOpenPortal = async () => {
  isPortalLoading.value = true
  errorMessage.value = ''

  try {
    await openBillingPortal()
  } catch (err) {
    errorMessage.value = err.message || t('subscription.portalError')
  } finally {
    isPortalLoading.value = false
  }
}

const isUpgradeDirection = (planId) => {
  const targetOrder = PLAN_ORDER[planId] || 0
  const currentOrder = PLAN_ORDER[subscription.value?.plan] || 0
  return targetOrder > currentOrder
}

const handleUpgrade = async (planId) => {
  errorMessage.value = ''

  // For paid users with active subscription, show confirmation dialog with proration preview
  if (subscription.value?.has_stripe_customer && subscription.value?.plan !== 'free' && subscription.value?.status === 'active') {
    isPreviewLoading.value = true
    upgradingPlan.value = planId
    try {
      const preview = await previewPlanChange(planId)
      prorationPreview.value = preview
      pendingPlanChange.value = planId
      showConfirmation.value = true
    } catch (err) {
      errorMessage.value = err.response?.data?.error || err.message || t('subscription.previewError')
    } finally {
      isPreviewLoading.value = false
      upgradingPlan.value = null
    }
    return
  }

  // For free users, go straight to checkout
  isUpgrading.value = true
  upgradingPlan.value = planId
  try {
    await startCheckout(planId)
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || t('subscription.checkoutError')
  } finally {
    isUpgrading.value = false
    upgradingPlan.value = null
  }
}

const confirmPlanChange = async () => {
  if (!pendingPlanChange.value) return

  isUpgrading.value = true
  upgradingPlan.value = pendingPlanChange.value
  errorMessage.value = ''

  try {
    await changePlan(pendingPlanChange.value)
    showConfirmation.value = false
    prorationPreview.value = null
    pendingPlanChange.value = null
    if (window.$toast) {
      window.$toast(t('subscription.planChanged'), 'success')
    }
    subscription.value = await fetchCurrentSubscription()
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || t('subscription.planChangeError')
  } finally {
    isUpgrading.value = false
    upgradingPlan.value = null
  }
}

const cancelConfirmation = () => {
  showConfirmation.value = false
  prorationPreview.value = null
  pendingPlanChange.value = null
}

const isPaidActive = computed(() => {
  return subscription.value &&
    ['starter', 'pro'].includes(subscription.value.plan) &&
    subscription.value.status === 'active' &&
    !subscription.value.cancel_at_period_end
})

const handleCancelSubscription = async () => {
  isCanceling.value = true
  errorMessage.value = ''

  try {
    await cancelSubscription()
    showCancelModal.value = false
    if (window.$toast) {
      window.$toast(t('subscription.cancelSuccess'), 'success')
    }
    subscription.value = await fetchCurrentSubscription()
  } catch (err) {
    errorMessage.value = err.response?.data?.error || err.message || t('subscription.cancelError')
  } finally {
    isCanceling.value = false
  }
}

const loadData = async () => {
  try {
    const [subscriptionData, plansData] = await Promise.all([
      fetchCurrentSubscription(),
      fetchPlans()
    ])
    subscription.value = subscriptionData
    availablePlans.value = plansData
  } catch (err) {
    errorMessage.value = err.message || t('subscription.loadError')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.subscription-page {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
  padding-bottom: var(--space-ma-xl);
}

/* ========================================
   PAGE HEADER
   ======================================== */
.page-header {
  padding: var(--space-ma-lg) 0 var(--space-ma);
}

.page-header h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: var(--space-sm);
}

.page-subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0;
}

/* ========================================
   LOADING STATE
   ======================================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-ma-xl);
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-md);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   SUBSCRIPTION SECTION
   ======================================== */
.subscription-section {
  margin-bottom: var(--space-ma);
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.section-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  flex-shrink: 0;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
}

.section-description {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
  margin: var(--space-xs) 0 0 0;
}

.settings-card {
  padding: var(--space-xl);
}

/* ========================================
   CURRENT PLAN CARD
   ======================================== */
.plan-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.plan-badge {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 500;
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.plan-badge.pro {
  background: linear-gradient(135deg, var(--color-ai) 0%, var(--color-ai-light) 100%);
  color: white;
}

.plan-badge.starter {
  background: var(--color-koke);
  color: white;
}

.status-badge {
  font-size: 0.75rem;
  font-weight: 500;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
}

.status-badge.active {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.status-badge.canceled {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.status-badge.past-due {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.status-badge.trialing {
  background: rgba(61, 90, 108, 0.15);
  color: var(--color-ai);
}

.plan-details {
  margin-bottom: var(--space-lg);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) 0;
}

.detail-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.detail-value {
  font-weight: 500;
  color: var(--color-sumi);
}

.detail-divider {
  height: 1px;
  background: var(--color-border-light);
}

.plan-features h4 {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  margin: 0 0 var(--space-md) 0;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-sm);
}

.features-list li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.features-list svg {
  color: var(--color-koke);
  flex-shrink: 0;
}

/* ========================================
   USAGE CARD
   ======================================== */
.usage-display {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.usage-number {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--space-xs);
}

.usage-current {
  font-family: var(--font-display);
  font-size: 3.5rem;
  font-weight: 400;
  color: var(--color-ai);
  line-height: 1;
}

.usage-separator {
  font-size: 2rem;
  color: var(--color-text-ghost);
}

.usage-limit {
  font-family: var(--font-display);
  font-size: 2rem;
  color: var(--color-text-tertiary);
}

.usage-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin-top: var(--space-sm);
  display: block;
}

.usage-progress {
  max-width: 400px;
  margin: 0 auto;
}

.progress-bar {
  height: 8px;
  background: var(--color-border-light);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--space-sm);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-ai) 0%, var(--color-ai-light) 100%);
  border-radius: 4px;
  transition: width 0.5s var(--easing-zen);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.unlimited-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: linear-gradient(135deg, var(--color-ai-subtle) 0%, rgba(61, 90, 108, 0.1) 100%);
  border-radius: var(--radius-md);
  color: var(--color-ai);
  font-weight: 500;
}

/* ========================================
   MANAGE CARD
   ======================================== */
.portal-section,
.upgrade-section {
  text-align: center;
}

.portal-info,
.upgrade-info {
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-lg) 0;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.upgrade-buttons {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  flex-wrap: wrap;
}

/* Button Spinner */
.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: var(--space-sm);
  vertical-align: middle;
}

.zen-btn-ai .btn-spinner {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

.zen-btn-filled .btn-spinner {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

/* Disabled visual state for buttons when another upgrade is in progress */
.zen-btn.is-loading-other {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* ========================================
   PLANS GRID
   ======================================== */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}

.plan-card {
  padding: var(--space-xl);
  position: relative;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.plan-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lifted);
}

.plan-card.current {
  border: 2px solid var(--color-ai);
}

.plan-card.recommended {
  border: 2px solid var(--color-ai);
}

.recommended-badge,
.current-badge {
  position: absolute;
  top: calc(-1 * var(--space-sm));
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  font-weight: 500;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
}

.recommended-badge {
  background: var(--color-ai);
  color: white;
}

.current-badge {
  background: var(--color-koke);
  color: white;
}

.plan-card h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0 0 var(--space-md) 0;
  text-align: center;
}

.plan-price {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.price-amount {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 400;
  color: var(--color-sumi);
}

.price-period {
  font-size: 0.9375rem;
  color: var(--color-text-tertiary);
}

.plan-features-list {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-lg) 0;
}

.plan-features-list li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  padding: var(--space-xs) 0;
}

.plan-features-list svg {
  color: var(--color-koke);
  flex-shrink: 0;
}

.plan-card .zen-btn {
  width: 100%;
}

/* ========================================
   PAYMENTS UNAVAILABLE BANNER
   ======================================== */
.payments-unavailable-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  background: var(--color-ai-subtle);
  border: 1px solid rgba(61, 90, 108, 0.2);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-ma);
}

.payments-unavailable-banner .banner-icon {
  color: var(--color-ai);
  flex-shrink: 0;
  margin-top: 2px;
}

.payments-unavailable-banner .banner-text strong {
  display: block;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
}

.payments-unavailable-banner .banner-text p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

/* ========================================
   CANCELLATION BANNER
   ======================================== */
.cancellation-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  background: rgba(184, 122, 94, 0.08);
  border: 1px solid rgba(184, 122, 94, 0.25);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-ma);
}

.cancellation-banner .banner-icon {
  color: var(--color-terra);
  flex-shrink: 0;
  margin-top: 2px;
}

.cancellation-banner .banner-text strong {
  display: block;
  color: var(--color-terra);
  margin-bottom: var(--space-xs);
}

.cancellation-banner .banner-text p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

/* ========================================
   ERROR MESSAGE
   ======================================== */
.error-message {
  padding: var(--space-md) var(--space-lg);
  background: rgba(184, 122, 94, 0.1);
  border: 1px solid var(--color-terra);
  border-radius: var(--radius-md);
  color: var(--color-terra);
  text-align: center;
  margin-top: var(--space-lg);
}

/* ========================================
   PLAN COMPARISON TABLE
   ======================================== */
.plan-comparison-table {
  padding: 0;
  overflow: hidden;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.comparison-table th,
.comparison-table td {
  padding: var(--space-md) var(--space-lg);
  text-align: center;
  border-bottom: 1px solid var(--color-border-light);
  vertical-align: middle;
}

.comparison-table thead th {
  background: var(--color-washi-warm);
  padding: var(--space-lg);
}

.comparison-table .feature-column {
  width: 200px;
  text-align: left;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.comparison-table .plan-column {
  min-width: 180px;
}

.comparison-table .current-plan {
  background: rgba(61, 90, 108, 0.05);
}

.comparison-table thead .current-plan {
  background: rgba(61, 90, 108, 0.1);
}

.comparison-table .recommended-plan {
  background: rgba(61, 90, 108, 0.03);
}

.plan-header-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
}

.table-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px var(--space-sm);
  border-radius: var(--radius-sm);
}

.table-badge.current {
  background: var(--color-ai);
  color: white;
}

.table-badge.recommended {
  background: linear-gradient(135deg, var(--color-ai) 0%, var(--color-ai-light) 100%);
  color: white;
}

.plan-name {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.plan-price-cell {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.feature-name {
  text-align: left !important;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.feature-value {
  font-weight: 600;
  color: var(--color-sumi);
}

.feature-value.highlight {
  color: var(--color-ai);
}

.check-icon {
  color: var(--color-koke);
  margin: 0 auto;
  display: block;
}

.check-icon.highlight {
  color: var(--color-ai);
}

.feature-limited {
  font-size: 0.8125rem;
  color: var(--color-terra);
  font-weight: 500;
}

.feature-unavailable {
  font-size: 1.25rem;
  color: var(--color-text-ghost);
}

.comparison-table tfoot td {
  padding: var(--space-lg);
  border-bottom: none;
  background: var(--color-washi-warm);
}

.upgrade-btn {
  width: 100%;
  max-width: 200px;
  font-size: 0.9375rem;
  padding: var(--space-sm) var(--space-md);
}

.current-plan-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  font-size: 0.875rem;
  color: var(--color-koke);
  font-weight: 500;
}

.current-plan-indicator svg {
  color: var(--color-koke);
}

/* Mobile Plan Cards */
.mobile-only {
  display: none;
}

.plan-limit-badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: var(--space-md);
}

.upgrade-btn-large {
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  font-size: 1rem;
  font-weight: 500;
}

.current-plan-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  color: var(--color-koke);
  font-weight: 500;
  background: rgba(122, 139, 110, 0.1);
  border-radius: var(--radius-md);
}

.current-plan-text svg {
  color: var(--color-koke);
}

/* ========================================
   CONFIRMATION MODAL
   ======================================== */
.modal-overlay {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-md);
}

.modal {
  width: 100%;
  max-width: 480px;
  padding: var(--space-xl);
  animation: modal-enter 0.2s var(--easing-zen);
}

.modal:hover {
  transform: none;
  box-shadow: var(--shadow-paper);
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.modal-close {
  padding: var(--space-xs);
  background: transparent;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.modal-close:hover {
  background: var(--color-bg-secondary);
  color: var(--color-sumi);
}

.modal-body {
  margin-bottom: var(--space-lg);
}

.plan-transition {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.plan-transition-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
}

.plan-transition-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
}

.plan-transition-name {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--color-sumi);
}

.plan-transition-name.highlight {
  color: var(--color-ai);
}

.plan-transition-arrow {
  color: var(--color-text-ghost);
  flex-shrink: 0;
}

.proration-details {
  background: var(--color-washi-warm);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-lg);
}

.proration-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) 0;
}

.proration-label {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

/* ========================================
   MWST HINT
   ======================================== */
.mwst-hint {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text-tertiary);
  margin-left: var(--space-xs);
}

.plan-price .mwst-hint {
  display: block;
  margin-left: 0;
  margin-top: var(--space-xs);
}

/* ========================================
   PAYMENT FAILED BANNER
   ======================================== */
.payment-failed-banner {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  background: rgba(184, 80, 60, 0.08);
  border: 1px solid rgba(184, 80, 60, 0.3);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-ma);
}

.payment-failed-banner .banner-icon {
  color: var(--color-terra);
  flex-shrink: 0;
}

.payment-failed-banner .banner-content {
  flex: 1;
}

.payment-failed-banner .banner-content strong {
  display: block;
  color: var(--color-terra);
  margin-bottom: var(--space-xs);
}

.payment-failed-banner .banner-content p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.proration-value {
  font-weight: 500;
  color: var(--color-sumi);
}

.proration-divider {
  height: 1px;
  background: var(--color-border-light);
}

.proration-explanation {
  margin-bottom: var(--space-md);
}

.proration-explanation p {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  line-height: var(--leading-normal);
  margin: 0;
}

.payment-failed-banner .banner-action {
  flex-shrink: 0;
  white-space: nowrap;
}

/* ========================================
   CANCEL SECTION
   ======================================== */
.cancel-icon {
  background: rgba(184, 122, 94, 0.1);
  color: var(--color-terra);
}

.cancel-card {
  text-align: center;
}

.zen-btn-danger {
  background: transparent;
  color: var(--color-terra);
  border: 1px solid var(--color-terra);
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-base), color var(--transition-base);
}

.zen-btn-danger:hover {
  background: var(--color-terra);
  color: white;
}

.zen-btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.zen-btn-danger .btn-spinner {
  border-color: currentColor;
  border-top-color: transparent;
}

/* ========================================
   CANCEL MODAL
   ======================================== */
.cancel-modal {
  max-width: 480px;
  width: 100%;
  padding: var(--space-xl);
}

.cancel-modal h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0 0 var(--space-md) 0;
  color: var(--color-sumi);
}

.modal-description {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-xl) 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}

/* ========================================
   DARK MODE
   ======================================== */
:global(.dark-mode) .payment-failed-banner {
  background: rgba(184, 80, 60, 0.12);
  border-color: rgba(184, 80, 60, 0.35);
}

:global(.dark-mode) .cancel-modal {
  background: var(--color-washi);
}

:global(.dark-mode) .modal-overlay {
  background: rgba(0, 0, 0, 0.7);
}

:global(.dark-mode) .zen-btn-danger:hover {
  background: var(--color-terra);
  color: white;
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .plan-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .features-list {
    grid-template-columns: 1fr;
  }

  .upgrade-buttons {
    flex-direction: column;
  }

  .upgrade-buttons .zen-btn {
    width: 100%;
  }

  .plans-grid {
    grid-template-columns: 1fr;
  }

  .payment-failed-banner {
    flex-direction: column;
    text-align: center;
  }

  .payment-failed-banner .banner-action {
    width: 100%;
  }

  .modal-actions {
    flex-direction: column-reverse;
  }

  .modal-actions .zen-btn {
    width: 100%;
  }

  /* Hide table on mobile, show cards */
  .plan-comparison-table {
    display: none;
  }

  .mobile-only {
    display: grid;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .section-header {
    flex-direction: column;
  }

  .usage-current {
    font-size: 2.5rem;
  }

  .usage-limit {
    font-size: 1.5rem;
  }

  .modal {
    max-width: 100%;
    padding: var(--space-lg);
  }

  .modal-body {
    max-height: 60vh;
    overflow-y: auto;
  }

  .plan-transition {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .plan-transition-arrow {
    transform: rotate(90deg);
  }

  .modal-actions {
    flex-direction: column-reverse;
  }

  .modal-actions .zen-btn {
    width: 100%;
  }
}
</style>
