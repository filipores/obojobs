<template>
  <div class="applications-page">
    <div class="container">
      <!-- Header Section -->
      <section class="page-header animate-fade-up">
        <div class="page-header-content">
          <div>
            <h1>Bewerbungen</h1>
            <p class="page-subtitle">Verwalten und verfolgen Sie alle Ihre Bewerbungen</p>
          </div>
          <div class="export-section">
            <label class="export-filter-toggle" v-if="hasActiveFilters">
              <input type="checkbox" v-model="exportFilteredOnly" />
              <span>Nur gefilterte ({{ filteredApplications.length }})</span>
            </label>
            <div class="export-buttons">
              <button
                @click="exportApplications('csv')"
                class="zen-btn zen-btn-sm"
                :disabled="isExportDisabled"
                :title="exportDisabledReason"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                CSV
              </button>
              <button
                @click="exportApplications('pdf')"
                class="zen-btn zen-btn-sm"
                :disabled="isExportDisabled"
                :title="exportDisabledReason"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                PDF
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Stats Section -->
      <section class="stats-section animate-fade-up" style="animation-delay: 100ms;">
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ totalApplications }}</span>
            <span class="stat-label">Gesamt</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.erstellt }}</span>
            <span class="stat-label">Erstellt</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.versendet }}</span>
            <span class="stat-label">Versendet</span>
          </div>
        </div>
      </section>

      <!-- Status Filter Tabs -->
      <section class="status-tabs-section animate-fade-up" style="animation-delay: 125ms;">
        <div class="status-tabs" role="tablist" aria-label="Status-Filter">
          <button
            v-for="status in statusOptions"
            :key="status.value"
            :class="['status-tab', { 'status-tab-active': filterStatus === status.value }]"
            @click="filterStatus = status.value"
            role="tab"
            :aria-selected="filterStatus === status.value"
            :aria-controls="'applications-list'"
          >
            <span class="status-tab-label">{{ status.label }}</span>
            <span class="status-tab-count">{{ status.count }}</span>
          </button>
        </div>
      </section>

      <!-- Filter Section -->
      <section class="filter-section animate-fade-up" style="animation-delay: 150ms;">
        <div class="filter-row">
          <div class="search-group">
            <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              v-model="searchInput"
              type="text"
              placeholder="Suche nach Firma oder Position..."
              class="form-input search-input"
            />
          </div>
          <div class="filter-group sort-group">
            <select v-model="sortBy" class="form-select">
              <option value="datum_desc">Datum (neueste zuerst)</option>
              <option value="datum_asc">Datum (älteste zuerst)</option>
              <option value="firma_asc">Firma (A-Z)</option>
              <option value="firma_desc">Firma (Z-A)</option>
              <option value="status">Status</option>
            </select>
          </div>
          <div class="view-toggle" role="group" aria-label="Ansicht wechseln">
            <button
              :class="['view-toggle-btn', { active: viewMode === 'grid' }]"
              @click="viewMode = 'grid'"
              :aria-pressed="viewMode === 'grid'"
              title="Karten-Ansicht"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
              </svg>
            </button>
            <button
              :class="['view-toggle-btn', { active: viewMode === 'table' }]"
              @click="viewMode = 'table'"
              :aria-pressed="viewMode === 'table'"
              title="Tabellen-Ansicht"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="searchQuery || filterStatus || filterFirma" class="active-filters">
          <span v-if="searchQuery" class="filter-tag">
            "{{ searchQuery }}"
            <button @click="searchInput = ''; searchQuery = ''" class="filter-tag-close">&times;</button>
          </span>
          <span v-if="filterStatus" class="filter-tag">
            {{ getStatusLabel(filterStatus) }}
            <button @click="filterStatus = ''" class="filter-tag-close">&times;</button>
          </span>
          <span v-if="filterFirma" class="filter-tag filter-tag-firma">
            Firma: {{ filterFirma }}
            <button @click="clearFilters" class="filter-tag-close">&times;</button>
          </span>
        </div>
      </section>

      <!-- Ink Stroke -->
      <div class="ink-stroke"></div>

      <!-- Loading State - Skeleton -->
      <div v-if="loading" class="loading-skeleton" aria-label="Lade Bewerbungen">
        <div class="skeleton-grid">
          <div v-for="i in 6" :key="i" class="skeleton-card zen-card">
            <div class="skeleton-card-header">
              <div class="skeleton-title-group">
                <div class="skeleton skeleton-company"></div>
                <div class="skeleton skeleton-position"></div>
              </div>
              <div class="skeleton skeleton-status"></div>
            </div>
            <div class="skeleton-card-meta">
              <div class="skeleton skeleton-date"></div>
              <div class="skeleton skeleton-source"></div>
            </div>
            <div class="skeleton skeleton-notes"></div>
            <div class="skeleton-card-actions">
              <div class="skeleton skeleton-btn-sm"></div>
              <div class="skeleton skeleton-btn-sm"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="error-state">
        <div class="error-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <h3>Fehler beim Laden der Bewerbungen</h3>
        <p>Es gab ein technisches Problem beim Laden Ihrer Bewerbungen. Bitte versuchen Sie es erneut.</p>
        <button @click="loadApplications()" class="zen-btn zen-btn-ai">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
          </svg>
          Erneut versuchen
        </button>
      </div>

      <!-- Applications Grid -->
      <section v-else-if="filteredApplications.length > 0" class="applications-section">
        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="applications-grid">
          <div
            v-for="app in filteredApplications"
            :key="app.id"
            class="application-card zen-card stagger-item"
            @click="openDetails(app)"
          >
            <div class="card-header">
              <div class="card-title-group">
                <h3>{{ app.firma }}</h3>
                <p class="card-position">{{ app.position || 'Position nicht angegeben' }}</p>
              </div>
              <span :class="['status-badge', `status-${app.status}`]">
                {{ getStatusLabel(app.status) }}
              </span>
            </div>

            <div class="card-meta">
              <span class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
                {{ formatDate(app.datum) }}
              </span>
              <span v-if="app.quelle" class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                </svg>
                {{ getDomain(app.quelle) }}
              </span>
            </div>

            <div v-if="app.notizen" class="card-notes">
              {{ app.notizen.slice(0, 80) }}{{ app.notizen.length > 80 ? '...' : '' }}
            </div>

            <div class="card-actions" @click.stop>
              <button @click="downloadPDF(app.id)" class="zen-btn zen-btn-sm">
                PDF
              </button>
              <button @click="openDetails(app)" class="zen-btn zen-btn-ai zen-btn-sm">
                Details
              </button>
            </div>
          </div>
        </div>

        <!-- Table View -->
        <ScrollableTable v-else class="applications-table-wrapper">
          <table class="applications-table">
            <thead>
              <tr>
                <th
                  @click="toggleTableSort('firma')"
                  @keydown="handleSortKeydown($event, 'firma')"
                  class="sortable-header"
                  tabindex="0"
                  role="columnheader"
                  aria-sort="none"
                >
                  Firma
                  <span v-if="sortBy.startsWith('firma')" class="sort-indicator">
                    {{ sortBy === 'firma_asc' ? '↑' : '↓' }}
                  </span>
                </th>
                <th>Position</th>
                <th
                  @click="toggleTableSort('datum')"
                  @keydown="handleSortKeydown($event, 'datum')"
                  class="sortable-header"
                  tabindex="0"
                  role="columnheader"
                  aria-sort="none"
                >
                  Datum
                  <span v-if="sortBy.startsWith('datum')" class="sort-indicator">
                    {{ sortBy === 'datum_asc' ? '↑' : '↓' }}
                  </span>
                </th>
                <th
                  @click="toggleTableSort('status')"
                  @keydown="handleSortKeydown($event, 'status')"
                  class="sortable-header"
                  tabindex="0"
                  role="columnheader"
                  aria-sort="none"
                >
                  Status
                  <span v-if="sortBy === 'status'" class="sort-indicator">●</span>
                </th>
                <th>Quelle</th>
                <th class="actions-header">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="app in filteredApplications"
                :key="app.id"
                class="table-row"
                @click="openDetails(app)"
              >
                <td class="cell-firma">{{ app.firma }}</td>
                <td class="cell-position">{{ app.position || '–' }}</td>
                <td class="cell-datum">{{ formatDate(app.datum) }}</td>
                <td class="cell-status">
                  <span :class="['status-badge status-badge-sm', `status-${app.status}`]">
                    {{ getStatusLabel(app.status) }}
                  </span>
                </td>
                <td class="cell-quelle">
                  <a v-if="app.quelle" :href="app.quelle" target="_blank" @click.stop class="table-link">
                    {{ getDomain(app.quelle) }}
                  </a>
                  <span v-else class="text-muted">–</span>
                </td>
                <td class="cell-actions" @click.stop>
                  <button @click="downloadPDF(app.id)" class="zen-btn zen-btn-sm" title="PDF herunterladen">
                    PDF
                  </button>
                  <button @click="openDetails(app)" class="zen-btn zen-btn-ai zen-btn-sm" title="Details anzeigen">
                    Details
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </ScrollableTable>

        <!-- Pagination -->
        <nav v-if="totalPages > 1" class="pagination" aria-label="Bewerbungs-Seitennavigation">
          <button
            class="pagination-btn"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
            aria-label="Vorherige Seite"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>

          <div class="pagination-pages">
            <button
              v-if="currentPage > 2"
              class="pagination-btn pagination-page"
              @click="goToPage(1)"
            >
              1
            </button>
            <span v-if="currentPage > 3" class="pagination-ellipsis">...</span>

            <button
              v-for="page in visiblePages"
              :key="page"
              class="pagination-btn pagination-page"
              :class="{ 'pagination-page-active': page === currentPage }"
              @click="goToPage(page)"
              :aria-current="page === currentPage ? 'page' : undefined"
            >
              {{ page }}
            </button>

            <span v-if="currentPage < totalPages - 2" class="pagination-ellipsis">...</span>
            <button
              v-if="currentPage < totalPages - 1"
              class="pagination-btn pagination-page"
              @click="goToPage(totalPages)"
            >
              {{ totalPages }}
            </button>
          </div>

          <button
            class="pagination-btn"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
            aria-label="Nächste Seite"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </nav>

        <p v-if="totalPages > 1" class="pagination-info">
          Seite {{ currentPage }} von {{ totalPages }} ({{ totalApplications }} Bewerbungen)
        </p>
      </section>

      <!-- Empty State -->
      <section v-else class="empty-state">
        <div class="empty-enso"></div>
        <h3>{{ searchQuery || filterStatus || filterFirma ? 'Keine Ergebnisse' : 'Noch keine Bewerbungen' }}</h3>
        <p v-if="searchQuery || filterStatus || filterFirma">
          Keine Bewerbungen gefunden. Versuchen Sie andere Suchbegriffe.
        </p>
        <p v-else>
          Generieren Sie Ihre erste Bewerbung über die Chrome Extension.
        </p>
        <button v-if="searchQuery || filterStatus || filterFirma" @click="clearFilters" class="zen-btn">
          Filter zurücksetzen
        </button>
      </section>

      <!-- Detail Modal -->
      <Teleport to="body">
        <div v-if="selectedApp" class="modal-overlay" @click="closeDetails">
          <div class="modal zen-card animate-fade-up" @click.stop>
            <div class="modal-header">
              <div>
                <h2>{{ selectedApp.firma }}</h2>
                <p class="modal-subtitle">{{ selectedApp.position }}</p>
              </div>
              <button @click="closeDetails" class="modal-close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div class="modal-content">
              <!-- Status -->
              <div class="detail-group detail-group-highlight">
                <label class="detail-label">Status</label>
                <select v-model="selectedApp.status" @change="updateStatus(selectedApp)" class="form-select">
                  <option value="erstellt">Erstellt</option>
                  <option value="versendet">Versendet</option>
                  <option value="antwort_erhalten">Antwort erhalten</option>
                  <option value="absage">Absage</option>
                  <option value="zusage">Zusage</option>
                </select>
              </div>

              <!-- Info Grid -->
              <div class="info-grid">
                <div class="detail-group">
                  <label class="detail-label">Firma</label>
                  <p class="detail-value">{{ selectedApp.firma }}</p>
                </div>

                <div v-if="selectedApp.position" class="detail-group">
                  <label class="detail-label">Position</label>
                  <p class="detail-value">{{ selectedApp.position }}</p>
                </div>

                <div v-if="selectedApp.ansprechpartner" class="detail-group">
                  <label class="detail-label">Ansprechpartner</label>
                  <p class="detail-value">{{ selectedApp.ansprechpartner }}</p>
                </div>

                <div v-if="selectedApp.email" class="detail-group">
                  <label class="detail-label">Email</label>
                  <p class="detail-value">
                    <a :href="`mailto:${selectedApp.email}`" class="detail-link">{{ selectedApp.email }}</a>
                  </p>
                </div>

                <div v-if="selectedApp.quelle" class="detail-group">
                  <label class="detail-label">Quelle</label>
                  <p class="detail-value">
                    <a :href="selectedApp.quelle" target="_blank" class="detail-link">{{ getDomain(selectedApp.quelle) }}</a>
                  </p>
                </div>

                <div class="detail-group">
                  <label class="detail-label">Datum</label>
                  <p class="detail-value">{{ formatDateTime(selectedApp.datum) }}</p>
                </div>
              </div>

              <!-- Sent Info -->
              <div v-if="selectedApp.sent_at" class="detail-group detail-group-sent">
                <label class="detail-label">Gesendet</label>
                <p class="detail-value">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="sent-icon">
                    <path d="M22 2L11 13"/>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
                  </svg>
                  {{ formatDateTime(selectedApp.sent_at) }} via {{ getSentViaLabel(selectedApp.sent_via) }}
                </p>
              </div>

              <!-- Betreff -->
              <div v-if="selectedApp.betreff" class="detail-group">
                <label class="detail-label">Betreff</label>
                <p class="detail-value detail-value-block">{{ selectedApp.betreff }}</p>
              </div>

              <!-- Notes -->
              <div class="detail-group">
                <label class="detail-label">Notizen</label>
                <textarea
                  v-model="selectedApp.notizen"
                  @blur="updateNotes(selectedApp)"
                  placeholder="Notizen hinzufügen..."
                  rows="4"
                  class="form-textarea"
                ></textarea>
              </div>

              <!-- Interview Tracking Section -->
              <div class="detail-group">
                <label class="detail-label">Interview-Tracking</label>
                <InterviewTracker
                  :application-id="selectedApp.id"
                  :initial-date="selectedApp.interview_date"
                  :initial-result="selectedApp.interview_result"
                  :initial-feedback="selectedApp.interview_feedback"
                  @updated="onInterviewUpdated"
                />
              </div>

              <!-- ATS Optimizer Section -->
              <div class="detail-group">
                <label class="detail-label">ATS-Optimierung</label>
                <ATSOptimizer
                  v-if="selectedApp.id"
                  :application-id="selectedApp.id"
                  @optimized="onATSOptimized"
                />
              </div>

              <!-- Gap Analysis / Learning Recommendations Section -->
              <div class="detail-group">
                <label class="detail-label">Skill-Luecken & Lernempfehlungen</label>
                <div v-if="jobFitLoading" class="gap-loading-state">
                  <div class="loading-spinner"></div>
                  <span>Lade Skill-Analyse...</span>
                </div>
                <GapAnalysis
                  v-else-if="jobFitData"
                  :recommendations="jobFitData.learning_recommendations || []"
                  :missing-skills="jobFitData.missing_skills || []"
                  :partial-matches="jobFitData.partial_matches || []"
                  :loading="false"
                />
                <div v-else class="gap-empty-state">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  <div>
                    <strong>Keine Skill-Analyse verfuegbar</strong>
                    <p>Analysieren Sie zuerst die Stellenanforderungen, um Skill-Luecken und Lernempfehlungen zu erhalten.</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <router-link
                :to="`/applications/${selectedApp.id}/interview`"
                class="zen-btn zen-btn-interview"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                Interview-Prep
              </router-link>
              <button @click="openEmailComposer(selectedApp)" class="zen-btn zen-btn-ai">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
                {{ selectedApp.sent_at ? 'Erneut senden' : 'Email senden' }}
              </button>
              <button @click="downloadPDF(selectedApp.id)" class="zen-btn">
                PDF herunterladen
              </button>
              <button @click="deleteApp(selectedApp.id)" class="zen-btn zen-btn-danger" aria-label="Bewerbung löschen" title="Bewerbung löschen">
                Löschen
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Email Composer Modal -->
      <Teleport to="body">
        <div v-if="showEmailComposer && emailComposerApp" class="modal-overlay" @click="closeEmailComposer">
          <div class="modal email-composer-modal zen-card animate-fade-up" @click.stop>
            <div class="modal-header">
              <div class="modal-header-content">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
                <div>
                  <h2>Bewerbung versenden</h2>
                  <p class="modal-subtitle">{{ emailComposerApp.firma }} - {{ emailComposerApp.position }}</p>
                </div>
              </div>
              <button @click="closeEmailComposer" class="modal-close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div class="modal-content">
              <!-- No accounts warning -->
              <div v-if="!hasConnectedAccounts" class="warning-box">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <div>
                  <strong>Kein E-Mail-Konto verbunden</strong>
                  <p>Verbinde zuerst ein Gmail- oder Outlook-Konto in den <router-link to="/settings">Einstellungen</router-link>.</p>
                </div>
              </div>

              <!-- Edit Mode -->
              <div v-if="!isPreviewMode" class="email-form">
                <!-- Account Selector -->
                <div v-if="hasConnectedAccounts" class="form-group">
                  <label class="form-label">Absender</label>
                  <select v-model="selectedEmailAccountId" class="form-select account-selector">
                    <option v-for="account in emailAccounts" :key="account.id" :value="account.id">
                      <span>{{ account.email }}</span> ({{ account.provider === 'gmail' ? 'Gmail' : 'Outlook' }})
                    </option>
                  </select>
                </div>

                <!-- To Field -->
                <div class="form-group">
                  <label class="form-label">An</label>
                  <input
                    v-model="emailForm.to"
                    type="email"
                    placeholder="email@beispiel.de"
                    class="form-input"
                    :class="{ 'input-warning': !emailComposerApp?.email && !emailForm.to }"
                  />
                  <p v-if="!emailComposerApp?.email && !emailForm.to" class="field-hint warning">
                    Keine Kontakt-Email in Bewerbungsdaten gefunden. Bitte manuell eingeben.
                  </p>
                </div>

                <!-- Subject Field -->
                <div class="form-group">
                  <label class="form-label">Betreff</label>
                  <input
                    v-model="emailForm.subject"
                    type="text"
                    placeholder="Bewerbung als..."
                    class="form-input"
                  />
                </div>

                <!-- Body Field -->
                <div class="form-group">
                  <label class="form-label">Nachricht</label>
                  <textarea
                    v-model="emailForm.body"
                    rows="12"
                    placeholder="Ihre Nachricht..."
                    class="form-textarea email-body-textarea"
                  ></textarea>
                </div>

                <!-- Attachment Info -->
                <div class="attachment-info">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                  </svg>
                  <span>Anschreiben (PDF) und Lebenslauf werden automatisch angehängt</span>
                </div>
              </div>

              <!-- Preview Mode -->
              <div v-else class="email-preview">
                <div class="preview-header">
                  <div class="preview-row">
                    <span class="preview-label">Von:</span>
                    <span class="preview-value">{{ getSelectedAccount()?.email || 'Nicht ausgewählt' }}</span>
                  </div>
                  <div class="preview-row">
                    <span class="preview-label">An:</span>
                    <span class="preview-value">{{ emailForm.to || 'Keine Adresse' }}</span>
                  </div>
                  <div class="preview-row">
                    <span class="preview-label">Betreff:</span>
                    <span class="preview-value preview-subject">{{ emailForm.subject || 'Kein Betreff' }}</span>
                  </div>
                </div>
                <div class="preview-body">
                  <pre>{{ emailForm.body || 'Keine Nachricht' }}</pre>
                </div>
                <div class="preview-attachments">
                  <div class="preview-label">Anhänge:</div>
                  <div class="attachment-list">
                    <div class="attachment-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                      <span>Anschreiben_{{ emailComposerApp.firma }}.pdf</span>
                    </div>
                    <div class="attachment-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                      <span>Lebenslauf.pdf</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer email-composer-footer">
              <button @click="togglePreview" class="zen-btn">
                {{ isPreviewMode ? 'Bearbeiten' : 'Vorschau' }}
              </button>
              <div class="footer-actions">
                <button @click="closeEmailComposer" class="zen-btn">
                  Abbrechen
                </button>
                <button
                  @click="sendEmail"
                  :disabled="!hasConnectedAccounts || !emailForm.to || !emailForm.subject || isSendingEmail"
                  class="zen-btn zen-btn-ai"
                >
                  <span v-if="isSendingEmail">Wird gesendet...</span>
                  <span v-else>Senden</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import ATSOptimizer from '../components/ATSOptimizer.vue'
import GapAnalysis from '../components/GapAnalysis.vue'
import InterviewTracker from '../components/InterviewTracker.vue'
import ScrollableTable from '../components/ScrollableTable.vue'
import { confirm } from '../composables/useConfirm'
import { getFullLocale } from '../i18n'

const route = useRoute()
const router = useRouter()

const applications = ref([])
const selectedApp = ref(null)
const loading = ref(false)
const loadError = ref(false)
const searchInput = ref('')  // What user types (for v-model)
const searchQuery = ref('')  // What filtering uses (debounced)
let searchTimeout = null
const filterStatus = ref('')
const filterFirma = ref('')
const sortBy = ref('datum_desc')
const exportFilteredOnly = ref(false)
const viewMode = ref(localStorage.getItem('applications_view_mode') || 'grid')

// Pagination State
const currentPage = ref(1)
const totalPages = ref(1)
const totalApplications = ref(0)
const perPage = ref(15)

// Email Composer State
const showEmailComposer = ref(false)
const emailComposerApp = ref(null)
const emailAccounts = ref([])
const selectedEmailAccountId = ref(null)
const emailForm = ref({
  to: '',
  subject: '',
  body: ''
})
const isPreviewMode = ref(false)
const isSendingEmail = ref(false)

// Job-Fit / Gap Analysis State
const jobFitData = ref(null)
const jobFitLoading = ref(false)

const stats = computed(() => {
  return {
    erstellt: applications.value.filter(a => a.status === 'erstellt').length,
    versendet: applications.value.filter(a => a.status === 'versendet').length
  }
})

const statusOptions = computed(() => {
  const counts = {
    '': applications.value.length,
    'erstellt': applications.value.filter(a => a.status === 'erstellt').length,
    'versendet': applications.value.filter(a => a.status === 'versendet').length,
    'antwort_erhalten': applications.value.filter(a => a.status === 'antwort_erhalten').length,
    'absage': applications.value.filter(a => a.status === 'absage').length,
    'zusage': applications.value.filter(a => a.status === 'zusage').length
  }
  return [
    { value: '', label: 'Alle', count: counts[''] },
    { value: 'erstellt', label: 'Erstellt', count: counts['erstellt'] },
    { value: 'versendet', label: 'Versendet', count: counts['versendet'] },
    { value: 'antwort_erhalten', label: 'Antwort', count: counts['antwort_erhalten'] },
    { value: 'absage', label: 'Absage', count: counts['absage'] },
    { value: 'zusage', label: 'Zusage', count: counts['zusage'] }
  ]
})

const filteredApplications = computed(() => {
  let filtered = applications.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(app =>
      app.firma.toLowerCase().includes(query) ||
      (app.position && app.position.toLowerCase().includes(query))
    )
  }

  if (filterStatus.value) {
    filtered = filtered.filter(app => app.status === filterStatus.value)
  }

  if (filterFirma.value) {
    filtered = filtered.filter(app => app.firma === filterFirma.value)
  }

  // Sortierung anwenden
  return [...filtered].sort((a, b) => {
    switch (sortBy.value) {
      case 'datum_desc':
        return new Date(b.datum) - new Date(a.datum)
      case 'datum_asc':
        return new Date(a.datum) - new Date(b.datum)
      case 'firma_asc':
        return a.firma.localeCompare(b.firma, 'de')
      case 'firma_desc':
        return b.firma.localeCompare(a.firma, 'de')
      case 'status': {
        const statusOrder = ['zusage', 'antwort_erhalten', 'versendet', 'erstellt', 'absage']
        return statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status)
      }
      default:
        return new Date(b.datum) - new Date(a.datum)
    }
  })
})

const hasActiveFilters = computed(() => {
  return !!(searchQuery.value || filterStatus.value || filterFirma.value)
})

const isExportDisabled = computed(() => {
  // Disabled wenn keine Bewerbungen vorhanden
  if (applications.value.length === 0) return true
  // Disabled wenn "Nur gefilterte" aktiv und 0 Ergebnisse
  if (exportFilteredOnly.value && filteredApplications.value.length === 0) return true
  return false
})

const exportDisabledReason = computed(() => {
  if (applications.value.length === 0) {
    return 'Keine Bewerbungen zum Exportieren vorhanden'
  }
  if (exportFilteredOnly.value && filteredApplications.value.length === 0) {
    return 'Keine gefilterten Ergebnisse zum Exportieren'
  }
  return ''
})

// Pagination: visible page numbers
const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 1)
  const end = Math.min(totalPages.value, currentPage.value + 1)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const loadApplications = async (page = 1) => {
  loading.value = true
  loadError.value = false
  try {
    const { data } = await api.silent.get('/applications', {
      params: {
        page,
        per_page: perPage.value
      }
    })
    applications.value = data.applications || []
    currentPage.value = data.page || 1
    totalPages.value = data.pages || 1
    totalApplications.value = data.total || 0
    loadError.value = false
  } catch (err) {
    console.error('Fehler beim Laden:', err)
    loadError.value = true
    applications.value = []
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    loadApplications(page)
  }
}

const downloadPDF = async (id) => {
  try {
    window.open(`/api/applications/${id}/pdf`, '_blank')
  } catch (_e) {
    alert('Fehler beim PDF-Download')
  }
}

const openDetails = (app) => {
  selectedApp.value = { ...app }
  loadJobFitData(app.id)
}

const loadJobFitData = async (appId) => {
  jobFitData.value = null
  jobFitLoading.value = true
  try {
    const { data } = await api.get(`/applications/${appId}/job-fit?include_recommendations=true`)
    if (data.success) {
      jobFitData.value = data.job_fit
    }
  } catch (err) {
    // Silently fail - job fit data is optional
    console.log('Job-Fit Daten nicht verfuegbar:', err.response?.data?.error || err.message)
  } finally {
    jobFitLoading.value = false
  }
}

const closeDetails = () => {
  selectedApp.value = null
}

const updateStatus = async (app) => {
  try {
    await api.put(`/applications/${app.id}`, {
      status: app.status
    })
    const index = applications.value.findIndex(a => a.id === app.id)
    if (index !== -1) {
      applications.value[index].status = app.status
    }
    if (window.$toast) {
      window.$toast('Status erfolgreich geändert', 'success')
    }
  } catch (_e) {
    alert('Fehler beim Aktualisieren')
  }
}

const updateNotes = async (app) => {
  try {
    await api.put(`/applications/${app.id}`, {
      notizen: app.notizen
    })
    const index = applications.value.findIndex(a => a.id === app.id)
    if (index !== -1) {
      applications.value[index].notizen = app.notizen
    }
  } catch (_e) {
    alert('Fehler beim Speichern der Notizen')
  }
}

const deleteApp = async (id) => {
  const confirmed = await confirm({
    title: 'Bewerbung löschen',
    message: 'Möchten Sie diese Bewerbung wirklich löschen?',
    confirmText: 'Löschen',
    cancelText: 'Abbrechen',
    type: 'danger'
  })
  if (!confirmed) return

  try {
    await api.delete(`/applications/${id}`)
    if (selectedApp.value && selectedApp.value.id === id) {
      selectedApp.value = null
    }
    // Reload current page (or go back one page if empty)
    const pageToLoad = applications.value.length === 1 && currentPage.value > 1
      ? currentPage.value - 1
      : currentPage.value
    loadApplications(pageToLoad)
  } catch (_e) {
    alert('Fehler beim Löschen')
  }
}

const clearFilters = () => {
  searchInput.value = ''
  searchQuery.value = ''
  filterStatus.value = ''
  filterFirma.value = ''
  // Remove query params from URL
  if (route.query.firma) {
    router.replace({ path: '/applications' })
  }
}

const toggleTableSort = (field) => {
  if (field === 'firma') {
    sortBy.value = sortBy.value === 'firma_asc' ? 'firma_desc' : 'firma_asc'
  } else if (field === 'datum') {
    sortBy.value = sortBy.value === 'datum_desc' ? 'datum_asc' : 'datum_desc'
  } else if (field === 'status') {
    sortBy.value = 'status'
  }
}

// Keyboard handler for sortable headers
const handleSortKeydown = (event, field) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleTableSort(field)
  }
}

const onATSOptimized = (data) => {
  // Reload application data after optimization
  if (selectedApp.value && data.optimized_text) {
    selectedApp.value.email_text = data.optimized_text
  }
}

const onInterviewUpdated = (updatedApp) => {
  // Update both selectedApp and applications list
  if (selectedApp.value) {
    selectedApp.value.interview_date = updatedApp.interview_date
    selectedApp.value.interview_result = updatedApp.interview_result
    selectedApp.value.interview_feedback = updatedApp.interview_feedback
  }
  const index = applications.value.findIndex(a => a.id === updatedApp.id)
  if (index !== -1) {
    applications.value[index] = { ...applications.value[index], ...updatedApp }
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatDateTime = (date) => {
  return new Date(date).toLocaleString(getFullLocale(), {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getDomain = (url) => {
  try {
    const domain = new URL(url).hostname
    return domain.replace('www.', '')
  } catch {
    return url
  }
}

const getStatusLabel = (status) => {
  const labels = {
    'erstellt': 'Erstellt',
    'versendet': 'Versendet',
    'antwort_erhalten': 'Antwort',
    'absage': 'Absage',
    'zusage': 'Zusage'
  }
  return labels[status] || status
}

const getSentViaLabel = (provider) => {
  const labels = {
    'gmail': 'Gmail',
    'outlook': 'Outlook'
  }
  return labels[provider] || provider
}

const exportApplications = async (format) => {
  try {
    // Build query parameters
    const params = new URLSearchParams({ format })

    // Add filter parameters if exporting filtered only
    if (exportFilteredOnly.value && hasActiveFilters.value) {
      if (searchQuery.value) params.append('search', searchQuery.value)
      if (filterStatus.value) params.append('status', filterStatus.value)
      if (filterFirma.value) params.append('firma', filterFirma.value)
    }

    const response = await api.get(`/applications/export?${params}`, {
      responseType: 'blob'
    })
    // Create download link
    const blob = new Blob([response.data], {
      type: format === 'pdf' ? 'application/pdf' : 'text/csv'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const today = new Date().toISOString().split('T')[0]
    const suffix = exportFilteredOnly.value && hasActiveFilters.value ? '_gefiltert' : ''
    link.download = `bewerbungen${suffix}_${today}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (_e) {
    alert('Fehler beim Export')
  }
}

// Email Composer Functions
const loadEmailAccounts = async () => {
  try {
    const { data } = await api.get('/email/accounts')
    emailAccounts.value = data.data || []
    if (emailAccounts.value.length > 0) {
      selectedEmailAccountId.value = emailAccounts.value[0].id
    }
  } catch (err) {
    console.error('Fehler beim Laden der Email-Konten:', err)
  }
}

const replaceTemplateVariables = (text, app) => {
  if (!text) return ''
  return text
    .replace(/\{\{FIRMA\}\}/g, app.firma || '')
    .replace(/\{\{POSITION\}\}/g, app.position || '')
    .replace(/\{\{ANSPRECHPARTNER\}\}/g, app.ansprechpartner || '')
    .replace(/\{\{QUELLE\}\}/g, app.quelle || '')
}

const openEmailComposer = (app) => {
  emailComposerApp.value = { ...app }
  emailForm.value = {
    to: app.email || '',
    subject: replaceTemplateVariables(app.betreff, app),
    body: replaceTemplateVariables(app.email_text, app)
  }
  isPreviewMode.value = false
  isSendingEmail.value = false
  showEmailComposer.value = true
  loadEmailAccounts()
}

const closeEmailComposer = () => {
  showEmailComposer.value = false
  emailComposerApp.value = null
  isPreviewMode.value = false
}

const togglePreview = () => {
  isPreviewMode.value = !isPreviewMode.value
}

const getSelectedAccount = () => {
  return emailAccounts.value.find(a => a.id === selectedEmailAccountId.value)
}

const hasConnectedAccounts = computed(() => emailAccounts.value.length > 0)

const sendEmail = async () => {
  if (!emailComposerApp.value || !selectedEmailAccountId.value) return

  isSendingEmail.value = true

  try {
    await api.post('/email/send', {
      application_id: emailComposerApp.value.id,
      email_account_id: selectedEmailAccountId.value,
      to_email: emailForm.value.to,
      subject: emailForm.value.subject,
      body: emailForm.value.body,
      attachments: ['anschreiben', 'lebenslauf']
    })

    alert('Email erfolgreich gesendet!')
    closeEmailComposer()
    loadApplications()
  } catch (err) {
    const errorMsg = err.response?.data?.error || 'Fehler beim Senden der Email'
    alert(errorMsg)
  } finally {
    isSendingEmail.value = false
  }
}

// Escape key handler for modals
const handleEscapeKey = (event) => {
  if (event.key === 'Escape') {
    if (showEmailComposer.value) {
      closeEmailComposer()
    } else if (selectedApp.value) {
      closeDetails()
    }
  }
}

onMounted(() => {
  // Check for firma query parameter from Company Insights
  if (route.query.firma) {
    filterFirma.value = route.query.firma
  }
  loadApplications()
  loadEmailAccounts()

  // Add escape key listener for modals
  document.addEventListener('keydown', handleEscapeKey)
})

onUnmounted(() => {
  // Clean up search debounce timeout
  if (searchTimeout) clearTimeout(searchTimeout)
  // Remove escape key listener
  document.removeEventListener('keydown', handleEscapeKey)
})

// Watch for route query changes
watch(() => route.query.firma, (newFirma) => {
  filterFirma.value = newFirma || ''
})

// Debounce search input
watch(searchInput, (newVal) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    searchQuery.value = newVal
  }, 300)
})

// Reset exportFilteredOnly when no filters are active
watch(hasActiveFilters, (isActive) => {
  if (!isActive) {
    exportFilteredOnly.value = false
  }
})

// Persist view mode preference
watch(viewMode, (newMode) => {
  localStorage.setItem('applications_view_mode', newMode)
})
</script>

<style scoped>
.applications-page {
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

.page-header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
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

.export-buttons {
  display: flex;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.export-buttons .zen-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.export-buttons .zen-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ========================================
   STATS SECTION
   ======================================== */
.stats-section {
  margin-bottom: var(--space-lg);
}

.stats-grid {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 500;
  color: var(--color-ai);
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-top: var(--space-xs);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-sand);
}

/* ========================================
   FILTER SECTION
   ======================================== */
.filter-section {
  margin-bottom: var(--space-ma);
}

.filter-row {
  display: flex;
  gap: var(--space-md);
}

.search-group {
  flex: 1;
  position: relative;
}

.search-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-stone);
  pointer-events: none;
}

.search-input {
  padding-left: calc(var(--space-md) + 26px);
}

.filter-group {
  min-width: 200px;
}

.sort-group {
  min-width: 220px;
}

.active-filters {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-ai-subtle);
  color: var(--color-ai);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
}

.filter-tag-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
}

.filter-tag-close:hover {
  opacity: 1;
}

.filter-tag-firma {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

/* ========================================
   LOADING SKELETON
   ======================================== */
.loading-skeleton {
  padding: var(--space-ma) 0;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-lg);
}

.skeleton-card {
  padding: var(--space-lg);
}

.skeleton-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.skeleton-title-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-company {
  width: 60%;
  height: 1.25rem;
}

.skeleton-position {
  width: 40%;
  height: 1rem;
}

.skeleton-status {
  width: 70px;
  height: 1.5rem;
  border-radius: var(--radius-sm);
}

.skeleton-card-meta {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-md);
}

.skeleton-date {
  width: 90px;
  height: 1rem;
}

.skeleton-source {
  width: 80px;
  height: 1rem;
}

.skeleton-notes {
  width: 100%;
  height: 60px;
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.skeleton-card-actions {
  display: flex;
  gap: var(--space-sm);
}

.skeleton-btn-sm {
  width: 60px;
  height: 2rem;
  border-radius: var(--radius-md);
}

.skeleton {
  background: linear-gradient(90deg, var(--color-washi-aged) 25%, var(--color-washi-warm) 50%, var(--color-washi-aged) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.8s ease infinite;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ========================================
   APPLICATIONS GRID
   ======================================== */
.applications-section {
  margin-top: var(--space-ma);
}

.applications-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-lg);
}

.application-card {
  padding: var(--space-lg);
  cursor: pointer;
  transition: all var(--transition-base);
}

.application-card:hover {
  border-color: var(--color-ai);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.card-title-group {
  flex: 1;
  min-width: 0;
}

.card-title-group h3 {
  font-size: 1.125rem;
  font-weight: 500;
  color: var(--color-sumi);
  margin: 0 0 var(--space-xs) 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-position {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ========================================
   STATUS BADGES
   ======================================== */
.status-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  white-space: nowrap;
}

.status-erstellt {
  background: var(--color-ai-subtle);
  color: var(--color-ai);
}

.status-versendet {
  background: rgba(184, 122, 94, 0.15);
  color: var(--color-terra);
}

.status-antwort_erhalten {
  background: rgba(122, 139, 110, 0.15);
  color: var(--color-koke);
}

.status-absage {
  background: rgba(180, 80, 80, 0.15);
  color: #b45050;
}

.status-zusage {
  background: var(--color-koke);
  color: var(--color-washi);
}

/* ========================================
   CARD META
   ======================================== */
.card-meta {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--space-md);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

.meta-item svg {
  color: var(--color-stone);
}

.card-notes {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.card-actions {
  display: flex;
  gap: var(--space-sm);
}

/* ========================================
   ERROR STATE
   ======================================== */
.error-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.error-icon {
  color: var(--color-terra);
  margin: 0 auto var(--space-lg);
}

.error-state h3 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
  color: var(--color-sumi);
}

.error-state p {
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
  line-height: var(--leading-relaxed);
}

.error-state .zen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

/* ========================================
   EMPTY STATE
   ======================================== */
.empty-state {
  text-align: center;
  padding: var(--space-ma-xl) 0;
}

.empty-enso {
  width: 100px;
  height: 100px;
  margin: 0 auto var(--space-lg);
  border: 2px solid var(--color-sand);
  border-width: 2px 3px 2px 2.5px;
  border-radius: 50%;
  opacity: 0.3;
}

.empty-state h3 {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: var(--space-sm);
}

.empty-state p {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-lg);
}

/* ========================================
   MODAL
   ======================================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(44, 44, 44, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-lg);
}

.modal {
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-xl);
  border-bottom: 1px solid var(--color-border-light);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0 0 var(--space-xs) 0;
}

.modal-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  padding: var(--space-xs);
  transition: color var(--transition-base);
}

.modal-close:hover {
  color: var(--color-sumi);
}

.modal-content {
  padding: var(--space-xl);
}

.detail-group {
  margin-bottom: var(--space-lg);
}

.detail-group-highlight {
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-ai);
}

.detail-group-sent {
  padding: var(--space-md);
  background: rgba(122, 139, 110, 0.1);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-koke);
}

.detail-group-sent .detail-value {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-koke);
  font-weight: 500;
}

.sent-icon {
  flex-shrink: 0;
}

.detail-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-xs);
}

.detail-value {
  margin: 0;
  color: var(--color-sumi);
  font-size: 1rem;
}

.detail-value-block {
  padding: var(--space-md);
  background: var(--color-washi);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
}

.detail-link {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.detail-link:hover {
  text-decoration: underline;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.modal-footer {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-washi);
}

/* ========================================
   RESPONSIVE
   ======================================== */
@media (max-width: 768px) {
  .page-header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .export-buttons {
    justify-content: flex-start;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-group {
    min-width: 100%;
  }

  .applications-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    flex-wrap: wrap;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .card-actions {
    flex-direction: column;
  }
}

/* ========================================
   EMAIL COMPOSER MODAL
   ======================================== */
.email-composer-modal {
  max-width: 720px;
}

.modal-header-content {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
}

.modal-header-content svg {
  color: var(--color-ai);
  flex-shrink: 0;
  margin-top: var(--space-xs);
}

/* Warning Box */
.warning-box {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: rgba(184, 122, 94, 0.1);
  border: 1px solid var(--color-terra);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.warning-box svg {
  flex-shrink: 0;
  color: var(--color-terra);
}

.warning-box strong {
  display: block;
  color: var(--color-terra);
  margin-bottom: var(--space-xs);
}

.warning-box p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
}

.warning-box a {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.warning-box a:hover {
  text-decoration: underline;
}

/* Email Form */
.email-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.form-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  margin-bottom: var(--space-sm);
}

.account-selector {
  background: var(--color-washi);
}

.email-body-textarea {
  min-height: 240px;
  line-height: var(--leading-relaxed);
  font-family: inherit;
  resize: vertical;
}

/* Input Warning State */
.input-warning {
  border-color: var(--color-terra);
}

/* Field Hint */
.field-hint {
  font-size: 0.8125rem;
  margin-top: var(--space-xs);
  color: var(--color-text-secondary);
}

.field-hint.warning {
  color: var(--color-terra);
}

/* Attachment Info */
.attachment-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-ai-subtle);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  color: var(--color-ai);
}

.attachment-info svg {
  flex-shrink: 0;
}

/* Email Preview */
.email-preview {
  background: var(--color-washi);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.preview-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.preview-row {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}

.preview-row:last-child {
  margin-bottom: 0;
}

.preview-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  min-width: 60px;
}

.preview-value {
  font-size: 0.9375rem;
  color: var(--color-sumi);
}

.preview-subject {
  font-weight: 500;
}

.preview-body {
  padding: var(--space-lg);
  max-height: 300px;
  overflow-y: auto;
}

.preview-body pre {
  margin: 0;
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: var(--leading-relaxed);
  color: var(--color-sumi);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.preview-attachments {
  padding: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
  background: var(--color-washi-warm);
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  color: var(--color-sumi);
}

.attachment-item svg {
  color: var(--color-ai);
  flex-shrink: 0;
}

/* Email Composer Footer */
.email-composer-footer {
  justify-content: space-between;
}

.footer-actions {
  display: flex;
  gap: var(--space-md);
}

/* Modal Footer Button with Icon */
.modal-footer .zen-btn svg {
  margin-right: var(--space-xs);
  vertical-align: middle;
}

/* Interview Prep Button */
.zen-btn-interview {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: rgba(138, 79, 125, 0.1);
  border-color: rgba(138, 79, 125, 0.3);
  color: #8a4f7d;
  text-decoration: none;
}

.zen-btn-interview:hover {
  background: rgba(138, 79, 125, 0.2);
  border-color: #8a4f7d;
}

@media (max-width: 768px) {
  .email-composer-modal {
    max-width: 100%;
  }

  .email-composer-footer {
    flex-direction: column;
    gap: var(--space-md);
  }

  .footer-actions {
    width: 100%;
    justify-content: stretch;
  }

  .footer-actions .zen-btn {
    flex: 1;
  }
}

/* Gap Analysis States */
.gap-loading-state {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-secondary);
}

.gap-loading-state .loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-ai);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.gap-empty-state {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-washi-aged);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.gap-empty-state svg {
  flex-shrink: 0;
  color: var(--color-ai);
  opacity: 0.7;
}

.gap-empty-state strong {
  display: block;
  color: var(--color-sumi);
  margin-bottom: var(--space-xs);
  font-size: 0.9375rem;
}

.gap-empty-state p {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* ========================================
   PAGINATION
   ======================================== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-ma);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border-light);
}

.pagination-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 40px;
  padding: var(--space-sm);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.pagination-btn:hover:not(:disabled) {
  background: var(--color-ai-subtle);
  border-color: var(--color-ai);
  color: var(--color-ai);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination-pages {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.pagination-page {
  font-weight: 500;
  font-size: 0.875rem;
}

.pagination-page-active {
  background: var(--color-ai);
  border-color: var(--color-ai);
  color: var(--color-washi);
}

.pagination-page-active:hover:not(:disabled) {
  background: var(--color-ai);
  color: var(--color-washi);
}

.pagination-ellipsis {
  padding: 0 var(--space-xs);
  color: var(--color-text-tertiary);
}

.pagination-info {
  text-align: center;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: var(--space-md);
}

@media (max-width: 480px) {
  .pagination {
    gap: var(--space-xs);
  }

  .pagination-btn {
    min-width: 36px;
    height: 36px;
  }

  .pagination-page {
    font-size: 0.8125rem;
  }
}

/* ========================================
   VIEW TOGGLE
   ======================================== */
.view-toggle {
  display: flex;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 38px;
  background: transparent;
  border: none;
  color: var(--color-stone);
  cursor: pointer;
  transition: all var(--transition-base);
}

.view-toggle-btn:hover {
  background: var(--color-washi-aged);
  color: var(--color-sumi);
}

.view-toggle-btn.active {
  background: var(--color-ai);
  color: var(--color-washi);
}

.view-toggle-btn:first-child {
  border-right: 1px solid var(--color-border);
}

/* ========================================
   TABLE VIEW
   ======================================== */
.applications-table-wrapper {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.applications-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375rem;
}

.applications-table thead {
  background: var(--color-washi-aged);
  border-bottom: 1px solid var(--color-border);
}

.applications-table th {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: var(--tracking-wider);
  text-transform: uppercase;
  color: var(--color-text-ghost);
  white-space: nowrap;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: color var(--transition-base);
}

.sortable-header:hover {
  color: var(--color-ai);
}

.sort-indicator {
  margin-left: var(--space-xs);
  color: var(--color-ai);
}

.actions-header {
  text-align: right;
}

.applications-table tbody tr {
  border-bottom: 1px solid var(--color-border-light);
  transition: background var(--transition-base);
  cursor: pointer;
}

.applications-table tbody tr:last-child {
  border-bottom: none;
}

.applications-table tbody tr:hover {
  background: var(--color-ai-subtle);
}

.applications-table td {
  padding: var(--space-md) var(--space-lg);
  vertical-align: middle;
}

.cell-firma {
  font-weight: 500;
  color: var(--color-sumi);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-position {
  color: var(--color-text-secondary);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-datum {
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.cell-status {
  white-space: nowrap;
}

.status-badge-sm {
  font-size: 0.625rem;
  padding: 2px var(--space-sm);
}

.cell-quelle {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-link {
  color: var(--color-ai);
  text-decoration: none;
  font-weight: 500;
}

.table-link:hover {
  text-decoration: underline;
}

.text-muted {
  color: var(--color-text-ghost);
}

.cell-actions {
  text-align: right;
  white-space: nowrap;
}

.cell-actions .zen-btn {
  margin-left: var(--space-xs);
}

/* Table Responsive */
@media (max-width: 1024px) {
  .applications-table {
    min-width: 700px;
  }
}

@media (max-width: 768px) {
  .view-toggle {
    display: none;
  }
}

/* ========================================
   STATUS FILTER TABS
   ======================================== */
.status-tabs-section {
  margin-bottom: var(--space-md);
}

.status-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.status-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.status-tab:hover {
  background: var(--color-washi-aged);
  border-color: var(--color-stone);
  color: var(--color-sumi);
}

.status-tab:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}

.status-tab-active {
  background: var(--color-ai);
  border-color: var(--color-ai);
  color: var(--color-washi);
}

.status-tab-active:hover {
  background: var(--color-ai-dark, #2d4a5a);
  border-color: var(--color-ai-dark, #2d4a5a);
  color: var(--color-washi);
}

.status-tab-label {
  white-space: nowrap;
}

.status-tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-xs);
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
}

.status-tab-active .status-tab-count {
  background: rgba(255, 255, 255, 0.25);
}

@media (max-width: 768px) {
  .status-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: var(--space-sm);
    -webkit-overflow-scrolling: touch;
  }

  .status-tab {
    flex-shrink: 0;
  }
}
</style>
