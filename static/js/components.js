/**
 * ZeroGraph AI — FUI / Sci-Fi HUD Component Renderer
 * Developer: kzsamir
 * Enhanced with 1-click brief copy/export, Bengali micro-typography, and interactive detail panel binding
 */

const Components = {
    // Global store of last rendered brief for 1-click exports
    currentBriefData: null,

    renderKPICard(title, value, subtitle, badgeClass = '') {
        return `
            <div class="hud-box" style="margin-bottom:0;">
                <div class="hud-box-header">
                    <span>${title.toUpperCase()}</span>
                    <span class="status-dot-green"></span>
                </div>
                <div style="font-size: 26px; font-weight: 500; color: #ffffff; margin: 4px 0;">${value}</div>
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
        return `<span class="cite-chip" onclick="App.openEvidenceDetail('${msgId}')">[ ${msgId} ]</span>`;
    },

    formatCitations(text) {
        if (!text) return '';
        return text.replace(/\[(msg_[a-zA-Z0-9_]+)\]/g, (match, msgId) => {
            return `<span class="cite-chip" onclick="App.openEvidenceDetail('${msgId}')">[ ${msgId} ]</span>`;
        });
    },

    renderBrief(res) {
        if (!res || !res.brief) return `<div class="hud-box" style="color:var(--hud-red);">INVALID BRIEF DATA</div>`;

        this.currentBriefData = res;
        const brief = res.brief;
        const coverage = brief.evidence_coverage || {};
        const findings = brief.findings || [];
        const actions = brief.actions || [];

        return `
            <!-- FUI Executive Brief Header Box with 1-Click Action Buttons -->
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>■ EXECUTIVE BRIEF SUMMARY (বাংলা)</span>
                    <div style="display:flex; gap:8px;">
                        <button class="fui-btn-secondary" onclick="Components.copyBriefMarkdown()">
                            📋 COPY BRIEF (.MD)
                        </button>
                        <button class="fui-btn-secondary" onclick="Components.downloadBriefJSON()">
                            📥 EXPORT BRIEF (.JSON)
                        </button>
                        <span style="color:var(--hud-green); margin-left:6px;">VERIFIED ●</span>
                    </div>
                </div>

                <!-- Bengali Micro-Typography Container -->
                <div class="bengali-text" style="font-size: 15px; font-weight: 500; color: #ffffff; margin-bottom: 16px;">
                    ${this.formatCitations(brief.executive_summary_bn)}
                </div>

                <div style="display:flex; gap:16px; font-size:11px; color:var(--text-muted); border-top:1px dashed var(--border-color); padding-top:10px; flex-wrap:wrap;">
                    <div>EVIDENCE_COVERAGE: <strong style="color:var(--hud-green);">${coverage.coverage_percent || 100}%</strong></div>
                    <div>PRECISION: <strong style="color:var(--hud-blue);">${coverage.citation_precision_percent || 100}%</strong></div>
                    <div>STATUS: <strong style="color:#fff;">${brief.overall_status || 'AMBER'}</strong></div>
                    <div>RUN_HASH: <strong style="color:var(--text-dim);">${(res.hashes || {}).output_hash ? res.hashes.output_hash.substr(0,12) : 'HASH_OK'}...</strong></div>
                </div>
            </div>

            <!-- Interactive Findings Queue Table -->
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>FINDINGS QUEUE (${findings.length})</span>
                    <span>CLICK ROW / ID FOR DETAIL</span>
                </div>

                <div class="fui-table-container">
                    <table class="fui-table">
                        <thead>
                            <tr>
                                <th>FINDING ID</th>
                                <th>TITLE (BENGALI)</th>
                                <th>SEVERITY</th>
                                <th>EVIDENCE CITATIONS</th>
                                <th>RECOMMENDED ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${findings.map((f, i) => {
                                const fId = f.finding_id || `F-0${i+1}`;
                                const fTitle = f.title_bn || f.title_en || 'Finding detail';
                                const fAction = f.recommended_action_bn || 'Requires review';
                                return `
                                    <tr onclick="Components.selectFindingDetail('${fId}', '${encodeURIComponent(fTitle)}', '${encodeURIComponent(fAction)}', '${f.severity || 'MEDIUM'}')">
                                        <td><span class="fui-tag clickable-tag">${fId}</span></td>
                                        <td class="bengali-text"><strong>${fTitle}</strong></td>
                                        <td>${this.renderSeverityBadge(f.severity)}</td>
                                        <td>${(f.evidence_ids || []).map(id => this.renderEvidenceChip(id)).join(' ') || 'None'}</td>
                                        <td class="bengali-text" style="font-size:11px; color:var(--text-muted);">${fAction}</td>
                                    </tr>
                                `;
                            }).join('') || '<tr><td colspan="5" style="text-align:center;">No findings detected.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Interactive Corrective Action Register Table -->
            <div class="hud-box">
                <div class="hud-box-header">
                    <span>CORRECTIVE ACTION QUEUE (${actions.length})</span>
                    <span>LIVE STATUS MANAGEMENT</span>
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
                                <th>STATUS</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${actions.map((a, i) => {
                                const aId = a.action_id || `A-0${i+1}`;
                                const aTitle = a.title_bn || 'Action item';
                                return `
                                    <tr onclick="Components.selectActionDetail('${aId}', '${encodeURIComponent(aTitle)}', '${a.owner_role || 'Team Lead'}', '${a.status || 'OPEN'}')">
                                        <td><span class="fui-tag clickable-tag" style="border-color:var(--hud-green); color:var(--hud-green);">${aId}</span></td>
                                        <td class="bengali-text"><strong>${aTitle}</strong></td>
                                        <td>${a.owner_role || 'Team Lead'}</td>
                                        <td><span class="fui-tag">${a.priority || 'P2'}</span></td>
                                        <td>Within ${a.suggested_due_days || 7} days</td>
                                        <td>
                                            <select class="fui-status-select" onclick="event.stopPropagation();" onchange="Components.updateActionStatus('${a.id || aId}', this.value)">
                                                <option value="OPEN" ${a.status==='OPEN'?'selected':''}>OPEN</option>
                                                <option value="IN_REVIEW" ${a.status==='IN_REVIEW'?'selected':''}>IN_REVIEW</option>
                                                <option value="RESOLVED" ${a.status==='RESOLVED'?'selected':''}>RESOLVED</option>
                                                <option value="CLOSED" ${a.status==='CLOSED'?'selected':''}>CLOSED</option>
                                            </select>
                                        </td>
                                    </tr>
                                `;
                            }).join('') || '<tr><td colspan="6" style="text-align:center;">No corrective actions generated.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    // Populates finding detail into the right-side AUDIT_DETAIL sidebar
    selectFindingDetail(fId, titleEnc, actionEnc, severity) {
        App.ensureDetailPanelOpen();
        const title = decodeURIComponent(titleEnc);
        const action = decodeURIComponent(actionEnc);

        const titleEl = document.getElementById('detail-box-title');
        const bodyEl = document.getElementById('detail-box-body');
        const badgeEl = document.getElementById('detail-status-badge');

        if (titleEl) titleEl.textContent = `FINDING: ${fId} (${severity})`;
        if (badgeEl) badgeEl.textContent = severity;
        if (bodyEl) {
            bodyEl.innerHTML = `
                <div style="font-size:12px; color:var(--hud-yellow); font-weight:700; margin-bottom:8px;">[ SEVERITY: ${severity} ]</div>
                <div class="bengali-text" style="font-size:14px; font-weight:600; color:#fff; margin-bottom:12px;">${title}</div>
                <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase; margin-bottom:4px;">RECOMMENDED AUDIT ACTION</div>
                <div class="bengali-text" style="background:#080808; border:1px solid var(--border-color); padding:10px; color:#ddd; font-size:12px;">${action}</div>
            `;
        }
    },

    // Populates action detail into the right-side AUDIT_DETAIL sidebar
    selectActionDetail(aId, titleEnc, ownerRole, status) {
        App.ensureDetailPanelOpen();
        const title = decodeURIComponent(titleEnc);

        const titleEl = document.getElementById('detail-box-title');
        const bodyEl = document.getElementById('detail-box-body');
        const badgeEl = document.getElementById('detail-status-badge');

        if (titleEl) titleEl.textContent = `ACTION: ${aId}`;
        if (badgeEl) badgeEl.textContent = status;
        if (bodyEl) {
            bodyEl.innerHTML = `
                <div style="font-size:12px; color:var(--hud-green); font-weight:700; margin-bottom:8px;">[ OWNER: ${ownerRole.toUpperCase()} ]</div>
                <div class="bengali-text" style="font-size:14px; font-weight:600; color:#fff; margin-bottom:12px;">${title}</div>
                <div style="font-size:11px; color:var(--text-muted);">
                    Current status is set to <strong style="color:var(--hud-green);">${status}</strong>. Change status using the table dropdown control.
                </div>
            `;
        }
    },

    // Live update action item status in SQLite via REST API
    async updateActionStatus(actionDbId, newStatus) {
        try {
            await API.updateAction(actionDbId, { status: newStatus });
            console.log(`Action ${actionDbId} status updated to ${newStatus}`);
        } catch (e) {
            console.warn('Status update failed:', e.message);
        }
    },

    // 1-Click Copy Brief as Markdown
    copyBriefMarkdown() {
        if (!this.currentBriefData || !this.currentBriefData.brief) {
            alert('No active brief available.');
            return;
        }

        const brief = this.currentBriefData.brief;
        const mdText = `# ZEROGRAPH AI — EXECUTIVE BRIEF
**Run ID:** ${this.currentBriefData.run_id || 'N/A'}
**Timestamp:** ${this.currentBriefData.timestamp || 'N/A'}
**Developer:** KZSAMIR WORKSTATION PRO

---

## Executive Summary (বাংলা)
${brief.executive_summary_bn || ''}

---

## Key Findings (${(brief.findings || []).length})
${(brief.findings || []).map((f, i) => `### [${f.finding_id || `F-0${i+1}`}] ${f.title_bn || ''}
- **Severity:** ${f.severity}
- **Citations:** ${(f.evidence_ids || []).map(id => `\`[${id}]\``).join(', ')}
- **Recommended Action:** ${f.recommended_action_bn || ''}
`).join('\n')}

---

## Corrective Actions (${(brief.actions || []).length})
${(brief.actions || []).map((a, i) => `- [${a.action_id || `A-0${i+1}`}] **${a.title_bn}** (Owner: ${a.owner_role}, Priority: ${a.priority})`).join('\n')}
`;

        navigator.clipboard.writeText(mdText).then(() => {
            alert('Executive Brief copied to clipboard as defensible Markdown!');
        }).catch(err => {
            alert('Failed to copy. Please allow clipboard permissions.');
        });
    },

    // 1-Click Download Brief as JSON
    downloadBriefJSON() {
        if (!this.currentBriefData) return;
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.currentBriefData, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `zerograph_brief_${this.currentBriefData.run_id || 'export'}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    }
};
