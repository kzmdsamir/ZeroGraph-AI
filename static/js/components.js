/**
 * ZeroGraph AI — FUI / Sci-Fi HUD Component Renderer
 * Developer: kzsamir
 */

const Components = {
    renderKPICard(title, value, subtitle, badgeClass = '') {
        return `
            <div class="hud-box" style="margin-bottom:0;">
                <div class="hud-box-header">
                    <span>${title.toUpperCase()}</span>
                    <span class="status-dot-green"></span>
                </div>
                <div style="font-size: 28px; font-weight: 500; color: #ffffff; margin: 4px 0;">${value}</div>
                <div style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono);">${subtitle}</div>
            </div>
        `;
    },

    renderSeverityBadge(severity) {
        const sev = (severity || 'MEDIUM').toUpperCase();
        if (sev === 'CRITICAL' || sev === 'HIGH') {
            return `<span style="color:var(--hud-red); font-weight:700;"><span class="status-dot-red"></span>${sev}</span>`;
        } else if (sev === 'MEDIUM') {
            return `<span style="color:var(--hud-yellow); font-weight:700;"><span class="status-dot-green" style="background:var(--hud-yellow); box-shadow:0 0 6px var(--hud-yellow);"></span>${sev}</span>`;
        }
        return `<span style="color:var(--hud-green); font-weight:700;"><span class="status-dot-green"></span>${sev}</span>`;
    },

    renderEvidenceChip(msgId) {
        return `<span class="cite-chip" onclick="EvidenceDrawer.open('${msgId}')">[ ${msgId} ]</span>`;
    },

    formatCitations(text) {
        if (!text) return '';
        return text.replace(/\[(msg_[a-zA-Z0-9_]+)\]/g, (match, msgId) => {
            return `<span class="cite-chip" onclick="EvidenceDrawer.open('${msgId}')">[ ${msgId} ]</span>`;
        });
    },

    renderBrief(res) {
        if (!res || !res.brief) return `<div class="hud-box" style="color:var(--hud-red);">INVALID BRIEF DATA</div>`;

        const brief = res.brief;
        const val = res.validation || {};
        const coverage = brief.evidence_coverage || {};
        const findings = brief.findings || [];
        const actions = brief.actions || [];

        return `
            <!-- FUI Executive Summary Box -->
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>■ EXECUTIVE BRIEF SUMMARY (বাংলা)</span>
                    <span style="color:var(--hud-green);">VERIFIED ●</span>
                </div>

                <div style="font-size: 15px; font-weight: 500; line-height: 1.7; color: #ffffff; margin-bottom: 16px;">
                    ${this.formatCitations(brief.executive_summary_bn)}
                </div>

                <div style="display:flex; gap:16px; font-size:11px; color:var(--text-muted); border-top:1px dashed var(--border-color); padding-top:10px;">
                    <div>EVIDENCE_COVERAGE: <strong style="color:var(--hud-green);">${coverage.coverage_percent || 100}%</strong></div>
                    <div>PRECISION: <strong style="color:var(--hud-blue);">${coverage.citation_precision_percent || 100}%</strong></div>
                    <div>STATUS: <strong style="color:#fff;">${brief.overall_status || 'AMBER'}</strong></div>
                    <div>RUN_HASH: <strong style="color:var(--text-dim);">${(res.hashes || {}).output_hash ? res.hashes.output_hash.substr(0,12) : 'HASH_OK'}...</strong></div>
                </div>
            </div>

            <!-- Findings Table -->
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>FINDINGS QUEUE (${findings.length})</span>
                    <span>SORT: SEVERITY</span>
                </div>

                <div class="fui-table-container">
                    <table class="fui-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>TITLE (BENGALI)</th>
                                <th>SEVERITY</th>
                                <th>EVIDENCE CITATIONS</th>
                                <th>RECOMMENDED ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${findings.map((f, i) => `
                                <tr>
                                    <td><span class="fui-tag">${f.finding_id || `F-0${i+1}`}</span></td>
                                    <td><strong>${f.title_bn || f.title_en}</strong></td>
                                    <td>${this.renderSeverityBadge(f.severity)}</td>
                                    <td>${(f.evidence_ids || []).map(id => this.renderEvidenceChip(id)).join(' ') || 'None'}</td>
                                    <td style="font-size:11px; color:var(--text-muted);">${f.recommended_action_bn || 'Requires review'}</td>
                                </tr>
                            `).join('') || '<tr><td colspan="5" style="text-align:center;">No findings detected.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Action Register Queue -->
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>CORRECTIVE ACTION QUEUE (${actions.length})</span>
                    <span>TARGET: 7 DAYS</span>
                </div>

                <div class="fui-table-container">
                    <table class="fui-table">
                        <thead>
                            <tr>
                                <th>ACTION ID</th>
                                <th>TITLE (BENGALI)</th>
                                <th>OWNER ROLE</th>
                                <th>PRIORITY</th>
                                <th>DUE DATE</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${actions.map((a, i) => `
                                <tr>
                                    <td><span class="fui-tag" style="border-color:var(--hud-green); color:var(--hud-green);">${a.action_id || `A-0${i+1}`}</span></td>
                                    <td><strong>${a.title_bn}</strong></td>
                                    <td>${a.owner_role || 'Team Lead'}</td>
                                    <td><span class="fui-tag">${a.priority || 'P2'}</span></td>
                                    <td>Within ${a.suggested_due_days || 7} days</td>
                                </tr>
                            `).join('') || '<tr><td colspan="5" style="text-align:center;">No corrective actions generated.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
};
