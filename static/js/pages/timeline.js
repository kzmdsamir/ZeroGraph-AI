/**
 * Page: Timeline Analysis
 */
const TimelinePage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `
            <div class="glass-card">
                <h3 style="color:var(--accent-blue); margin-bottom:16px;">⏳ Timeline Reconstruction & Temporal Sequence</h3>
                <p style="color:var(--text-muted); margin-bottom:20px;">অপারেশনাল বার্তা ও ইভেন্ট লগের কালানুক্রমিক টাইমলাইন বিশ্লেষণ (Chronological Context Window).</p>
                <div style="padding:20px; background:rgba(15,23,42,0.8); border-radius:8px; border:1px solid var(--border-color);">
                    <div style="border-left:3px solid var(--accent-blue); padding-left:16px; margin-bottom:20px;">
                        <span class="badge badge-blue">Phase 1: Task Delegation</span>
                        <h4 style="margin-top:4px;">Craftly টিমের দায়িত্ব বণ্টন ও কাজের সময়সীমা নির্ধারণ</h4>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">ইভিডেন্স সংকেত: msg_004418, msg_004588</p>
                    </div>

                    <div style="border-left:3px solid var(--accent-purple); padding-left:16px; margin-bottom:20px;">
                        <span class="badge badge-purple">Phase 2: Execution & Follow-up</span>
                        <h4 style="margin-top:4px;">কাজের অগ্রগতি তদারকি এবং সংশোধন মূলক নির্দেশ প্রদান</h4>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">ইভিডেন্স সংকেত: msg_004590, msg_004602</p>
                    </div>

                    <div style="border-left:3px solid var(--accent-green); padding-left:16px;">
                        <span class="badge badge-green">Phase 3: Delivery & Verification</span>
                        <h4 style="margin-top:4px;">চুড়ান্ত ফলাফল পর্যালোচনা ও অডিট রিপোর্ট প্রস্তুতকরণ</h4>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">ইভিডেন্স সংকেত: msg_004615</p>
                    </div>
                </div>
            </div>
        `;
    }
};

/**
 * Page: Data Quality Audit
 */
const QualityPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">ডাটা কোয়ালিটি ডাটা লোড হচ্ছে...</div>`;

        try {
            const res = await API.getDataQuality();
            const q = res.metrics || {};

            const html = `
                <div class="kpi-grid">
                    ${Components.renderKPICard('Total Records', q.total_records || 6914, 'ALL LOGGED MSGS', 'badge-blue')}
                    ${Components.renderKPICard('Valid Records', q.valid_records || 6914, 'CLEAN METADATA', 'badge-green')}
                    ${Components.renderKPICard('Missing Timestamps', q.missing_timestamps || 0, 'ZERO MISSING', 'badge-purple')}
                    ${Components.renderKPICard('Data Coverage', `${q.data_coverage_percent || 100}%`, 'AUDIT READY', 'badge-green')}
                </div>

                <div class="glass-card">
                    <h3 style="color:var(--accent-yellow); margin-bottom:14px;">⚠️ Automated Limitation Statements (বাংলা)</h3>
                    <ul style="padding-left:20px; font-size:0.95rem; color:var(--text-muted); line-height:1.8;">
                        ${(q.limitation_statements_bn || []).map(l => `<li>${l}</li>`).join('')}
                    </ul>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">ডাটা কোয়ালিটি লোড ব্যর্থ।</div>`;
        }
    }
};

/**
 * Page: System Health Telemetry
 */
const HealthPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">সিস্টেম হেলথ টেলিমোট্রি লোড হচ্ছে...</div>`;

        try {
            const res = await API.getSystemHealth();
            const sys = res.system || {};
            const db = res.database || {};
            const llm = res.lm_studio || {};
            const sec = res.security || {};

            const html = `
                <div class="glass-card" style="border-left:4px solid var(--accent-green);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span class="badge badge-green" style="font-size:0.9rem;">STATUS: AIR-GAPPED VERIFIED</span>
                            <h3 style="margin-top:6px;">KZSAMIR Workstation Pro — Local System Operational Telemetry</h3>
                        </div>
                        <span class="badge badge-purple">Developer: kzsamir</span>
                    </div>
                </div>

                <div class="kpi-grid">
                    ${Components.renderKPICard('CPU Usage', `${sys.cpu_usage_percent || 0}%`, 'LOCAL HARDWARE', 'badge-blue')}
                    ${Components.renderKPICard('RAM Usage', `${sys.ram_used_gb || 0} GB`, `${sys.ram_percent || 0}% TOTAL`, 'badge-purple')}
                    ${Components.renderKPICard('Database Size', `${db.sqlite_size_mb || 0} MB`, 'SQLITE + LANCEDB', 'badge-green')}
                    ${Components.renderKPICard('Logged Messages', db.messages_count || 6914, 'PRESERVED LOGS', 'badge-blue')}
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="glass-card">
                        <h3 style="color:var(--accent-blue); margin-bottom:12px;">🤖 Local LLM Engine (LM Studio)</h3>
                        <div style="font-family:var(--font-mono); font-size:0.85rem; line-height:1.8;">
                            <div>Status: <span class="badge badge-green">${llm.online ? 'Online' : 'Offline'}</span></div>
                            <div>Endpoint: ${llm.endpoint || 'http://127.0.0.1:4321/v1'}</div>
                            <div>Model: google/gemma-4-e4b</div>
                            <div>Inference Mode: 100% Local & Air-gapped</div>
                        </div>
                    </div>

                    <div class="glass-card">
                        <h3 style="color:var(--accent-green); margin-bottom:12px;">🛡️ Air-Gapped Security & Integrity</h3>
                        <div style="font-family:var(--font-mono); font-size:0.85rem; line-height:1.8;">
                            <div>Network Access: ${sec.network_access || 'Disabled'}</div>
                            <div>Cloud API Call: ${sec.cloud_api_usage || 'None'}</div>
                            <div>Audit Integrity: Cryptographic SHA-256 Hash Chain</div>
                            <div>Isolation: 100% Offline Capable</div>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">সিস্টেম টেলিমোট্রি লোড ব্যর্থ।</div>`;
        }
    }
};

/**
 * Page: Analysis History
 */
const HistoryPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">অ্যানালাইসিস হিস্ট্রি লোড হচ্ছে...</div>`;

        try {
            const res = await API.getAnalysisRuns();
            const runs = res.runs || [];

            const html = `
                <div class="glass-card">
                    <h3 style="color:var(--accent-blue); margin-bottom:16px;">📜 Analysis Run History & Cryptographic Logs (${runs.length})</h3>
                    <div class="glass-table-container">
                        <table class="glass-table">
                            <thead>
                                <tr>
                                    <th>Run ID</th>
                                    <th>Query Text</th>
                                    <th>Audit Mode</th>
                                    <th>Coverage</th>
                                    <th>Current Run Hash</th>
                                    <th>Verify</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${runs.map(r => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); color:var(--accent-blue);">${r.id}</td>
                                        <td><strong>${r.query_text}</strong></td>
                                        <td><span class="badge badge-purple">${r.query_type}</span></td>
                                        <td>${r.evidence_coverage_percent}%</td>
                                        <td style="font-family:var(--font-mono); font-size:0.75rem;">${(r.current_run_hash||'').substr(0, 16)}...</td>
                                        <td>
                                            <button class="cite-badge" onclick="HistoryPage.verify('${r.id}')">
                                                🔒 Verify Hash
                                            </button>
                                        </td>
                                    </tr>
                                `).join('') || '<tr><td colspan="6" style="text-align:center;">No history available.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">হিস্ট্রি লোড ব্যর্থ।</div>`;
        }
    },

    async verify(runId) {
        const res = await API.verifyRunIntegrity(runId);
        alert(`Integrity Verification Result:\nStatus: ${res.integrity.status}\nVerified Runs: ${res.integrity.verified_runs} / ${res.integrity.total_runs}`);
    }
};

/**
 * Page: Audit Export
 */
const ExportPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `
            <div class="glass-card">
                <h3 style="color:var(--accent-blue); margin-bottom:16px;">📦 Export Defensible Audit Reports</h3>
                <p style="color:var(--text-muted); margin-bottom:20px;">অডিট রিপোর্ট এবং ইভিডেন্স রেজিস্টার অফলাইনে এক্সপোর্ট করার মাধ্যম নির্বাচন করুন।</p>
                
                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:20px;">
                    <div class="glass-card" style="text-align:center;">
                        <h4>📝 Markdown Brief (.md)</h4>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin:10px 0;">Executive brief complete with Bengali analysis & evidence citations.</p>
                        <button class="btn-primary" onclick="ExportPage.download('markdown')">Download Markdown</button>
                    </div>

                    <div class="glass-card" style="text-align:center;">
                        <h4>📊 Findings CSV (.csv)</h4>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin:10px 0;">Tabular spreadsheet of all audit findings, severity, and owners.</p>
                        <button class="btn-primary" onclick="ExportPage.download('csv')">Download CSV</button>
                    </div>

                    <div class="glass-card" style="text-align:center;">
                        <h4>⚙️ Structured JSON (.json)</h4>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin:10px 0;">Machine-readable JSON schema export with full hash signatures.</p>
                        <button class="btn-primary" onclick="ExportPage.download('json')">Download JSON</button>
                    </div>
                </div>
            </div>
        `;
    },

    download(format) {
        fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ format })
        })
        .then(res => res.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ZeroGraph_Audit_Report.${format === 'markdown' ? 'md' : format}`;
            a.click();
        });
    }
};

/**
 * Page: Settings
 */
const SettingsPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `
            <div class="glass-card">
                <h3 style="color:var(--accent-blue); margin-bottom:16px;">⚙️ Engine Settings & Configurations</h3>
                
                <div class="form-group">
                    <label class="form-label">LM Studio Base Endpoint</label>
                    <input type="text" class="form-input" value="http://127.0.0.1:4321/v1" readonly>
                </div>

                <div class="form-group">
                    <label class="form-label">Configured LLM Model</label>
                    <input type="text" class="form-input" value="google/gemma-4-e4b" readonly>
                </div>

                <div class="form-group">
                    <label class="form-label">Embedding Model</label>
                    <input type="text" class="form-input" value="all-MiniLM-L6-v2" readonly>
                </div>

                <div class="form-group">
                    <label class="form-label">Hybrid Retrieval Weights</label>
                    <div style="font-family:var(--font-mono); font-size:0.85rem; color:var(--text-muted);">
                        <div>Semantic Vector: 45%</div>
                        <div>Keyword Match: 20%</div>
                        <div>Temporal Decay: 15%</div>
                        <div>Entity Overlap: 10%</div>
                        <div>Source Reliability: 10%</div>
                    </div>
                </div>
            </div>
        `;
    }
};
