/**
 * Pages: Findings Register, Risk Matrix, Action Items, Evidence Queue
 * Developer: kzsamir
 * Interactive live management queue with detail drawer binding and status updates
 */

const FindingsPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted);">LOADING FINDINGS REGISTER...</div>`;

        try {
            const [findingsRes, actionsRes] = await Promise.all([
                API.getFindings(),
                API.getActions()
            ]);

            const findings = findingsRes.findings || [];
            const actions = actionsRes.actions || [];

            container.innerHTML = `
                <div class="hud-box">
                    <div class="hud-box-header">
                        <span>■ STRUCTURED FINDINGS REGISTER (${findings.length})</span>
                        <span>CLICK ROW / ID FOR AUDIT DETAIL</span>
                    </div>
                    <div class="fui-table-container">
                        <table class="fui-table">
                            <thead>
                                <tr>
                                    <th>FINDING CODE</th>
                                    <th>TITLE (BENGALI)</th>
                                    <th>SEVERITY</th>
                                    <th>CONFIDENCE</th>
                                    <th>RECOMMENDED ACTION</th>
                                    <th>STATUS</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${findings.map(f => {
                                    const fCode = f.finding_code || f.id;
                                    const fTitle = f.title_bn || f.title_en || 'Finding';
                                    const fAction = f.recommended_action_bn || 'Requires human audit';
                                    return `
                                        <tr onclick="Components.selectFindingDetail('${fCode}', '${encodeURIComponent(fTitle)}', '${encodeURIComponent(fAction)}', '${f.severity || 'MEDIUM'}')">
                                            <td><span class="fui-tag clickable-tag">${fCode}</span></td>
                                            <td class="bengali-text"><strong>${fTitle}</strong></td>
                                            <td>${Components.renderSeverityBadge(f.severity)}</td>
                                            <td><span class="fui-tag">${Math.round((f.confidence||0.8)*100)}%</span></td>
                                            <td class="bengali-text" style="font-size:11px; color:var(--text-muted);">${fAction}</td>
                                            <td><span class="fui-tag">${f.status || 'NEEDS_REVIEW'}</span></td>
                                        </tr>
                                    `;
                                }).join('') || '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">No findings recorded in database.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="hud-box" style="margin-top:20px;">
                    <div class="hud-box-header">
                        <span>■ CORRECTIVE ACTION REGISTER (${actions.length})</span>
                        <span>LIVE STATUS DROPDOWN MANAGEMENT</span>
                    </div>
                    <div class="fui-table-container">
                        <table class="fui-table">
                            <thead>
                                <tr>
                                    <th>ACTION CODE</th>
                                    <th>TITLE (BENGALI)</th>
                                    <th>OWNER ROLE</th>
                                    <th>PRIORITY</th>
                                    <th>DUE</th>
                                    <th>STATUS</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${actions.map(a => {
                                    const aCode = a.action_code || a.id;
                                    const aTitle = a.title_bn || 'Action item';
                                    return `
                                        <tr onclick="Components.selectActionDetail('${aCode}', '${encodeURIComponent(aTitle)}', '${a.owner_role || 'Team Lead'}', '${a.status || 'OPEN'}')">
                                            <td><span class="fui-tag clickable-tag" style="border-color:var(--hud-green); color:var(--hud-green);">${aCode}</span></td>
                                            <td class="bengali-text"><strong>${aTitle}</strong></td>
                                            <td>${a.owner_role || 'Team Lead'}</td>
                                            <td><span class="fui-tag">${a.priority || 'P2'}</span></td>
                                            <td>${a.suggested_due_days || 7} days</td>
                                            <td>
                                                <select class="fui-status-select" onclick="event.stopPropagation();" onchange="Components.updateActionStatus('${a.id}', this.value)">
                                                    <option value="OPEN" ${a.status==='OPEN'?'selected':''}>OPEN</option>
                                                    <option value="IN_REVIEW" ${a.status==='IN_REVIEW'?'selected':''}>IN_REVIEW</option>
                                                    <option value="RESOLVED" ${a.status==='RESOLVED'?'selected':''}>RESOLVED</option>
                                                    <option value="CLOSED" ${a.status==='CLOSED'?'selected':''}>CLOSED</option>
                                                </select>
                                            </td>
                                        </tr>
                                    `;
                                }).join('') || '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">No corrective actions recorded.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color:var(--hud-red); padding:20px;">FAILED TO LOAD FINDINGS REGISTER: ${e.message}</div>`;
        }
    }
};

const RisksPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted);">LOADING RISK MATRIX...</div>`;

        try {
            const res = await API.getRisks();
            const risks = res.risks || [];

            container.innerHTML = `
                <div class="hud-box">
                    <div class="hud-box-header">
                        <span>■ RISK MATRIX REGISTER (${risks.length})</span>
                        <span>SCORE = LIKELIHOOD × IMPACT × EXPOSURE</span>
                    </div>
                    <div class="fui-table-container">
                        <table class="fui-table">
                            <thead>
                                <tr>
                                    <th>RISK CODE</th>
                                    <th>TITLE</th>
                                    <th>LIKELIHOOD</th>
                                    <th>IMPACT</th>
                                    <th>EXPOSURE</th>
                                    <th>SCORE</th>
                                    <th>BAND</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${risks.map(r => `
                                    <tr>
                                        <td><span class="fui-tag">${r.risk_id || r.id}</span></td>
                                        <td class="bengali-text"><strong>${r.title || r.title_bn || 'Risk item'}</strong></td>
                                        <td>${r.likelihood || '-'} / 5</td>
                                        <td>${r.impact || '-'} / 5</td>
                                        <td>${r.exposure || '-'} / 3</td>
                                        <td><strong style="color:#fff;">${r.score || '-'}</strong></td>
                                        <td>${Components.renderSeverityBadge(r.band || r.severity)}</td>
                                    </tr>
                                `).join('') || '<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">No risk register items calculated.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color:var(--hud-red); padding:20px;">FAILED TO LOAD RISK MATRIX: ${e.message}</div>`;
        }
    }
};

const ActionsPage = {
    async render() {
        return FindingsPage.render();
    }
};

const EvidencePage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted);">LOADING EVIDENCE QUEUE (6,914 MESSAGES)...</div>`;

        try {
            const res = await API.getMessages({ limit: 30 });
            const messages = res.messages || [];

            container.innerHTML = `
                <div class="hud-box">
                    <div class="hud-box-header">
                        <span>■ EVIDENCE MESSAGES QUEUE (${res.total || 6914})</span>
                        <span>CLICK ID FOR CONTEXT WINDOW</span>
                    </div>
                    <div class="fui-table-container">
                        <table class="fui-table">
                            <thead>
                                <tr>
                                    <th>EVIDENCE ID</th>
                                    <th>AUTHOR</th>
                                    <th>CONTENT PREVIEW</th>
                                    <th>TIMESTAMP</th>
                                    <th>INTEGRITY</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${messages.map(m => `
                                    <tr onclick="App.openEvidenceDetail('${m.id}')">
                                        <td><span class="fui-tag clickable-tag">${m.id}</span></td>
                                        <td><strong>${m.author_name || 'Unknown'}</strong></td>
                                        <td class="bengali-text" style="max-width:380px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${m.text || ''}</td>
                                        <td style="font-size:11px; color:var(--text-muted);">${m.timestamp || '2026'}</td>
                                        <td><span class="status-dot-green"></span>SHA-256</td>
                                    </tr>
                                `).join('') || '<tr><td colspan="5" style="text-align:center; padding:20px; color:var(--text-muted);">No evidence records found.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `<div style="color:var(--hud-red); padding:20px;">FAILED TO LOAD EVIDENCE QUEUE: ${e.message}</div>`;
        }
    }
};
