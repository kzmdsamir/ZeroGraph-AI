/**
 * ZeroGraph AI — SPA Router & FUI Command Center Orchestrator
 * Developer: kzsamir
 * Direct Navigation Router with Animated Icon Integration & Search Bindings
 */

const App = {
    routes: {
        'executive': { title: 'Freight Queue', subtitle: 'DISPLAYING 6,914 OF 6,914 OPERATIONAL RECORDS', module: ExecutivePage },
        'intelligence': { title: 'Ask Operational Intelligence', subtitle: 'LOCAL LLM INFERENCE & HYBRID RETRIEVAL COMMAND ENGINE', module: IntelligencePage },
        'findings': { title: 'Findings Register', subtitle: 'STRUCTURED AUDIT FINDINGS & SEVERITY QUEUE', module: FindingsPage },
        'risks': { title: 'Risk Register', subtitle: 'MULTI-FACTOR LIKELIHOOD x IMPACT x EXPOSURE MATRIX', module: RisksPage },
        'actions': { title: 'Action Register', subtitle: 'CORRECTIVE ACTION QUEUE & VERIFICATION', module: ActionsPage },
        'evidence': { title: 'Evidence Explorer', subtitle: 'SEARCHABLE LOCAL EVIDENCE LOGS (6,914 RECORDS)', module: EvidencePage },
        'timeline': { title: 'Timeline Reconstruction', subtitle: 'CHRONOLOGICAL SEQUENCE & EVENT WINDOWS', module: TimelinePage },
        'quality': { title: 'Data Quality Audit', subtitle: 'COMPLETENESS METRICS & LIMITATION STATEMENTS', module: QualityPage },
        'health': { title: 'System Health Telemetry', subtitle: 'AIR-GAPPED LOCAL HARDWARE & MODEL TELEMETRY', module: HealthPage },
        'history': { title: 'Analysis History', subtitle: 'SHA-256 CRYPTOGRAPHIC HASH CHAIN AUDIT TRAIL', module: HistoryPage },
        'export': { title: 'Audit Export', subtitle: 'DEFENSIBLE MARKDOWN, CSV, AND JSON EXPORTS', module: ExportPage },
        'settings': { title: 'Engine Settings', subtitle: 'LOCAL MODEL & RETRIEVAL WEIGHT CONFIGURATION', module: SettingsPage }
    },

    init() {
        window.addEventListener('hashchange', () => this.handleRouting());
        this.handleRouting();
        this.updateTelemetry();
        this.bindGlobalSearch();
        setInterval(() => this.updateTelemetry(), 15000);
    },

    navigateTo(routeKey) {
        if (!this.routes[routeKey]) routeKey = 'executive';
        window.location.hash = `#${routeKey}`;
        this.handleRouting();
    },

    handleRouting() {
        let hash = window.location.hash.replace('#', '').trim();
        if (!hash || !this.routes[hash]) {
            hash = 'executive';
        }

        const routeConfig = this.routes[hash];

        const titleEl = document.getElementById('current-page-title');
        const subTitleEl = document.getElementById('current-page-subtitle');

        if (titleEl) titleEl.textContent = routeConfig.title;
        if (subTitleEl) subTitleEl.textContent = routeConfig.subtitle;

        // Active sidebar navigation button state
        document.querySelectorAll('.nav-item').forEach(el => {
            if (el.getAttribute('data-route') === hash) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });

        // Render page view module safely
        if (routeConfig.module && typeof routeConfig.module.render === 'function') {
            try {
                routeConfig.module.render();
            } catch (err) {
                console.error(`Error rendering page ${hash}:`, err);
            }
        }
    },

    toggleDetailPanel() {
        const grid = document.getElementById('main-workspace-grid');
        if (grid) {
            grid.classList.toggle('panel-collapsed');
        }
    },

    ensureDetailPanelOpen() {
        const grid = document.getElementById('main-workspace-grid');
        if (grid && grid.classList.contains('panel-collapsed')) {
            grid.classList.remove('panel-collapsed');
        }
    },

    openEvidenceDetail(msgId) {
        this.ensureDetailPanelOpen();
        EvidenceDrawer.open(msgId);
    },

    bindGlobalSearch() {
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) {
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const q = searchInput.value.trim();
                    if (q.startsWith('msg_') || q.startsWith('MSG_')) {
                        this.openEvidenceDetail(q);
                    } else if (q) {
                        this.navigateTo('intelligence');
                        setTimeout(() => {
                            const intelInput = document.getElementById('intel-query-input');
                            if (intelInput) {
                                intelInput.value = q;
                                if (typeof IntelligencePage.executeAnalysis === 'function') {
                                    IntelligencePage.executeAnalysis();
                                }
                            }
                        }, 100);
                    }
                }
            });
        }
    },

    async updateTelemetry() {
        try {
            const res = await API.getSystemHealth();
            const pillText = document.getElementById('telemetry-model-name');

            if (res.lm_studio && res.lm_studio.online) {
                if (pillText) pillText.textContent = `LIVE_CORE_ACTIVE (${res.lm_studio.model_configured || 'gemma-4-e4b'})`;
            } else {
                if (pillText) pillText.textContent = 'LOCAL_CORE_OFFLINE';
            }
        } catch (e) {
            // Fail silently on background telemetry
        }
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
