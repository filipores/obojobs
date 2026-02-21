<template>
  <div class="admin-users">
    <section class="admin-header">
      <div class="container">
        <div class="admin-header-content">
          <div>
            <span class="admin-label">Administration</span>
            <h1>{{ $t('admin.users.title') }}</h1>
          </div>
          <router-link to="/admin" class="zen-btn zen-btn-ghost">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            {{ $t('admin.users.backToDashboard') }}
          </router-link>
        </div>
      </div>
    </section>

    <section class="admin-controls-section">
      <div class="container">
        <div class="admin-controls">
          <div class="search-wrapper">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              v-model="search"
              @input="onSearch"
              type="text"
              class="zen-input search-input"
              :placeholder="$t('admin.users.searchPlaceholder')"
            />
          </div>
          <select v-model="planFilter" @change="onPlanFilter" class="zen-input plan-filter">
            <option value="">{{ $t('admin.users.allPlans') }}</option>
            <option value="free">Free</option>
            <option value="starter">Starter</option>
            <option value="pro">Pro</option>
          </select>
        </div>
      </div>
    </section>

    <section class="admin-table-section">
      <div class="container">
        <div class="table-wrapper">
          <table class="admin-table">
            <thead>
              <tr>
                <th @click="toggleSort('email')" class="sortable">
                  {{ $t('admin.users.email') }}
                  <span class="sort-indicator" v-if="sortField === 'email'">{{ sortOrder === 'asc' ? '&#9650;' : '&#9660;' }}</span>
                </th>
                <th @click="toggleSort('name')" class="sortable">
                  {{ $t('admin.users.name') }}
                  <span class="sort-indicator" v-if="sortField === 'name'">{{ sortOrder === 'asc' ? '&#9650;' : '&#9660;' }}</span>
                </th>
                <th @click="toggleSort('plan')" class="sortable">
                  {{ $t('admin.users.plan') }}
                  <span class="sort-indicator" v-if="sortField === 'plan'">{{ sortOrder === 'asc' ? '&#9650;' : '&#9660;' }}</span>
                </th>
                <th>{{ $t('admin.users.status') }}</th>
                <th @click="toggleSort('application_count')" class="sortable">
                  {{ $t('admin.users.applications') }}
                  <span class="sort-indicator" v-if="sortField === 'application_count'">{{ sortOrder === 'asc' ? '&#9650;' : '&#9660;' }}</span>
                </th>
                <th @click="toggleSort('created_at')" class="sortable">
                  {{ $t('admin.users.registered') }}
                  <span class="sort-indicator" v-if="sortField === 'created_at'">{{ sortOrder === 'asc' ? '&#9650;' : '&#9660;' }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading && users.length === 0">
                <td colspan="6" class="table-loading">{{ $t('admin.users.loading') }}</td>
              </tr>
              <tr v-else-if="users.length === 0">
                <td colspan="6" class="table-empty">{{ $t('admin.users.noUsers') }}</td>
              </tr>
              <tr
                v-for="user in users"
                :key="user.id"
                @click="goToUser(user.id)"
                class="user-row"
              >
                <td class="cell-email">{{ user.email }}</td>
                <td>{{ user.name || '–' }}</td>
                <td>
                  <span class="plan-badge" :class="'plan-' + (user.plan || 'free')">
                    {{ capitalize(user.plan || 'free') }}
                  </span>
                </td>
                <td>
                  <span class="status-dot" :class="{ active: user.is_active, inactive: !user.is_active }"></span>
                  {{ user.is_active ? $t('admin.users.active') : $t('admin.users.inactive') }}
                </td>
                <td>{{ user.application_count ?? 0 }}</td>
                <td>{{ formatDateDE(user.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="pages > 1" class="admin-pagination">
          <button @click="prevPage" :disabled="page <= 1" class="zen-btn zen-btn-ghost zen-btn-sm">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
            {{ $t('admin.users.previous') }}
          </button>
          <span class="pagination-info">{{ page }} / {{ pages }} ({{ total }} {{ $t('admin.users.usersTotal') }})</span>
          <button @click="nextPage" :disabled="page >= pages" class="zen-btn zen-btn-ghost zen-btn-sm">
            {{ $t('admin.users.next') }}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'
import { capitalize, formatDateDE } from '@/utils/format.js'

const router = useRouter()
const users = ref([])
const total = ref(0)
const page = ref(1)
const perPage = ref(20)
const pages = ref(1)
const search = ref('')
const planFilter = ref('')
const sortField = ref('created_at')
const sortOrder = ref('desc')
const loading = ref(false)

let searchTimeout = null

const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: perPage.value,
      sort: sortField.value,
      order: sortOrder.value,
    }
    if (search.value) params.search = search.value
    if (planFilter.value) params.plan = planFilter.value
    const { data } = await api.get('/admin/users', { params })
    users.value = data.users
    total.value = data.total
    pages.value = data.pages
  } catch (e) {
    console.error('Failed to load users:', e)
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => { page.value = 1; loadUsers() }, 300)
}

const onPlanFilter = () => { page.value = 1; loadUsers() }

const toggleSort = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
  }
  loadUsers()
}

const goToUser = (id) => router.push(`/admin/users/${id}`)
const prevPage = () => { if (page.value > 1) { page.value--; loadUsers() } }
const nextPage = () => { if (page.value < pages.value) { page.value++; loadUsers() } }

onMounted(loadUsers)
</script>

<style scoped>
.admin-users {
  min-height: calc(100vh - 73px);
  background: var(--color-washi);
}

/* ========================================
   ADMIN HEADER
   ======================================== */
.admin-header {
  padding: var(--space-ma-xl) 0 var(--space-ma);
}

.admin-header-content {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-lg);
}

.admin-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.admin-header h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 400;
  letter-spacing: -0.03em;
  margin-bottom: 0;
}

/* ========================================
   CONTROLS (Search + Filter)
   ======================================== */
.admin-controls-section {
  padding: 0 0 var(--space-ma);
}

.admin-controls {
  display: flex;
  gap: var(--space-md);
  align-items: center;
}

.search-wrapper {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-ghost);
  pointer-events: none;
}

.search-input {
  padding-left: 2.5rem !important;
  width: 100%;
}

.plan-filter {
  min-width: 140px;
}

/* ========================================
   TABLE
   ======================================== */
.admin-table-section {
  padding: 0 0 var(--space-ma-xl);
}

.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.admin-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-paper);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.admin-table th {
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  border-bottom: 1px solid var(--color-border-light);
  white-space: nowrap;
  user-select: none;
}

.admin-table th.sortable {
  cursor: pointer;
  transition: color var(--transition-base);
}

.admin-table th.sortable:hover {
  color: var(--color-ai);
}

.sort-indicator {
  font-size: 0.5rem;
  margin-left: var(--space-xs);
  color: var(--color-ai);
}

.admin-table td {
  padding: var(--space-md) var(--space-lg);
  font-size: 0.9375rem;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-light);
  white-space: nowrap;
}

.user-row {
  cursor: pointer;
  transition: background var(--transition-base);
}

.user-row:hover {
  background: var(--color-ai-subtle);
}

.user-row:last-child td {
  border-bottom: none;
}

.cell-email {
  font-weight: 500;
  color: var(--color-ai);
}

.table-loading,
.table-empty {
  text-align: center;
  padding: var(--space-xl) var(--space-lg) !important;
  color: var(--color-text-tertiary);
}

/* Plan Badge */
.plan-badge {
  display: inline-block;
  font-size: 0.6875rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full, 9999px);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.plan-free {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}

.plan-starter {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.plan-pro {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

/* Status Dot */
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: var(--space-xs);
  vertical-align: middle;
}

.status-dot.active {
  background: var(--color-success);
}

.status-dot.inactive {
  background: var(--color-error);
}

/* ========================================
   PAGINATION
   ======================================== */
.admin-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  padding: var(--space-lg) 0;
}

.pagination-info {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .admin-header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .admin-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .search-wrapper {
    max-width: 100%;
  }

  .plan-filter {
    min-width: 100%;
  }
}
</style>
