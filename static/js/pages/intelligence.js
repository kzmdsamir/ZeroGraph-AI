/**
 * Page: Ask Intelligence
 * Developer: kzsamir
 * Style: Sci-Fi FUI HUD Monospace Technical UI (Mobile Optimized)
 */
const IntelligencePage = {
    async render() {
        const container = document.getElementById('page-content');

        const html = `
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>■ LOCAL LLM INFERENCE QUERY ENGINE</span>
                    <span style="color:var(--hud-green);">STATUS: READY ●</span>
                </div>

                <div style="margin-bottom:14px;">
                    <label class="filter-label" style="display:block; margin-bottom:6px;">ENTER AUDIT QUERY / OPERATIONAL OBJECTIVE (BENGALI OR ENGLISH)</label>
                    <textarea id="intel-query-input" class="fui-input" style="background:#080808; border:1px solid var(--border-highlight); padding:12px; width:100%; min-height:70px; resize:vertical; font-family:var(--font-mono); line-height:1.5;" placeholder="e.g. টিম মেম্বারদের কাজ বণ্টন এবং সিদ্ধান্ত গ্রহণের প্রক্রিয়া বিশ্লেষণ করুন">টিম মেম্বারদের কাজ বণ্টন এবং সিদ্ধান্ত গ্রহণের প্রক্রিয়া বিশ্লেষণ করুন</textarea>
                </div>

                <div class="fui-form-grid" style="margin-bottom:16px;">
                    <div>
                        <label class="filter-label" style="display:block; margin-bottom:4px;">AUDIT MODE</label>
                        <select id="intel-mode-select" class="fui-select" style="width:100%;">
                            <option value="persuasion" selected>Persuasion & Communication Analysis</option>
                            <option value="general">General Intelligence Query</option>
                            <option value="operational_risk">Operational Risk Detection</option>
                            <option value="task_accountability">Task & Accountability</option>
                        </select>
                    </div>

                    <div>
                        <label class="filter-label" style="display:block; margin-bottom:4px;">TEMPERATURE</label>
                        <select id="intel-temp-select" class="fui-select" style="width:100%;">
                            <option value="0.1">0.1 (Strict Audit)</option>
                            <option value="0.2" selected>0.2 (Balanced Default)</option>
                        </select>
                    </div>

                    <div>
                        <label class="filter-label" style="display:block; margin-bottom:4px;">SEARCH DEPTH</label>
                        <select id="intel-depth-select" class="fui-select" style="width:100%;">
                            <option value="12" selected>12 Evidence Records</option>
                            <option value="15">15 Deep Records</option>
                        </select>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end;">
                    <button id="run-intel-btn" class="fui-btn fui-btn-full-mobile">
                        ⚡ RUN LOCAL ANALYSIS ENGINE
                    </button>
                </div>
            </div>

            <!-- Analysis Output Container -->
            <div id="intel-output-container">
                <div class="hud-box" style="text-align:center; padding:40px; color:var(--text-muted);">
                    Enter an audit query above and click "RUN LOCAL ANALYSIS ENGINE".
                </div>
            </div>
        `;

        container.innerHTML = html;
        document.getElementById('run-intel-btn').addEventListener('click', () => this.executeAnalysis());
    },

    async executeAnalysis() {
        const query = document.getElementById('intel-query-input').value.trim();
        const mode = document.getElementById('intel-mode-select').value;
        const temp = parseFloat(document.getElementById('intel-temp-select').value);

        if (!query) {
            alert('Please enter a query.');
            return;
        }

        const outputContainer = document.getElementById('intel-output-container');
        outputContainer.innerHTML = `
            <div class="hud-box" style="text-align:center; padding:40px;">
                <div style="color:var(--hud-green); font-size:14px; margin-bottom:8px;">
                    <span class="status-dot-green"></span> LOCAL LLM & HYBRID RETRIEVAL EXECUTION IN PROGRESS...
                </div>
                <div style="font-size:11px; color:var(--text-muted); word-break:break-word;">
                    LanceDB vector search -> SQLite graph context -> Local Gemma-4 inference...
                </div>
            </div>
        `;

        try {
            const res = await API.analyze({ query, mode, temperature: temp });
            if (!res.success) {
                outputContainer.innerHTML = `
                    <div class="hud-box" style="border-left:3px solid var(--hud-red);">
                        <div style="color:var(--hud-red); font-weight:700;">ANALYSIS EXECUTION ERROR</div>
                        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">${res.error || 'Local LLM error'}</div>
                    </div>
                `;
                return;
            }

            outputContainer.innerHTML = Components.renderBrief(res);

            // Update Right Detail Panel with analysis brief summary
            const titleEl = document.getElementById('detail-box-title');
            const bodyEl = document.getElementById('detail-box-body');
            const badgeEl = document.getElementById('detail-status-badge');

            if (titleEl) titleEl.textContent = `${res.run_id || 'RUN_OK'} / BRIEF COMPLETED`;
            if (bodyEl) bodyEl.innerHTML = Components.formatCitations(res.brief?.executive_summary_bn || 'Analysis finished successfully.');
            if (badgeEl) badgeEl.textContent = "VERIFIED";

        } catch (err) {
            outputContainer.innerHTML = `
                <div class="hud-box" style="border-left:3px solid var(--hud-red);">
                    <div style="color:var(--hud-red); font-weight:700;">NETWORK COMMUNICATION ERROR</div>
                </div>
            `;
        }
    }
};
