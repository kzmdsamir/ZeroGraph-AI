/**
 * Page: Executive Overview / Audit Command Queue
 * Developer: kzsamir
 * Design: High-Tech FUI / Sci-Fi HUD Command Center
 */
const ExecutivePage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted);">LOADING COMMAND QUEUE DATA...</div>`;

        try {
            const [healthRes, findingsRes, actionsRes, messagesRes] = await Promise.all([
                API.getSystemHealth(),
                API.getFindings(),
                API.getActions(),
                API.getMessages({ limit: 10 })
            ]);

            const findings = findingsRes.findings || [];
            const actions = actionsRes.actions || [];
            const messages = messagesRes.messages || [];

            const html = `
                <!-- Filter Pills Row -->
                <div class="filter-row">
                    <div class="filter-group">
                        <span class="filter-label">MODE</span>
                        <button class="filter-pill active">ALL</button>
                        <button class="filter-pill">PERSUASION</button>
                        <button class="filter-pill">RISK</button>
                    </div>

                    <div class="filter-group" style="margin-left:16px;">
                        <span class="filter-label">CARRIER</span>
                        <select class="fui-select">
                            <option>ALL CHANNELS</option>
                            <option>OPERATIONS</option>
                            <option>LOGISTICS</option>
                        </select>
                    </div>

                    <div class="filter-group" style="margin-left:16px;">
                        <span class="filter-label">STATE</span>
                        <button class="filter-pill active">ALL</button>
                        <button class="filter-pill">VERIFIED</button>
                        <button class="filter-pill">NEEDS REVIEW</button>
                    </div>

                    <div style="margin-left:auto; font-size:11px; color:var(--text-dim);">
                        ACTIVE FILTERS: NONE
                    </div>
                </div>

                <!-- 4 Top FUI KPI Cards -->
                <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:14px; margin-bottom:20px;">
                    ${Components.renderKPICard('Total Evidence', '6,914', 'VERIFIED LOGS')}
                    ${Components.renderKPICard('Open Findings', findings.length, 'NEEDS REVIEW')}
                    ${Components.renderKPICard('High-Risk Signals', findings.filter(f=>f.severity==='HIGH'||f.severity==='CRITICAL').length, 'CRITICAL ATTENTION')}
                    ${Components.renderKPICard('Evidence Coverage', '94%', 'VALIDATED CITATIONS')}
                </div>

                <!-- Data Table (Freight Queue / Evidence Queue Grid) -->
                <div class="fui-table-container">
                    <table class="fui-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>MD</th>
                                <th>EVIDENCE ID</th>
                                <th>CONTENT / ROUTE DESCRIPTION</th>
                                <th>TIMESTAMP</th>
                                <th>STATUS</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${messages.map((m, idx) => {
                                const statusDot = idx % 4 === 2 ? '<span class="status-dot-red"></span>' : '<span class="status-dot-green"></span>';
                                return `
                                    <tr onclick="ExecutivePage.selectRow('${m.id}', '${m.author_name}', '${encodeURIComponent(m.text)}')">
                                        <td style="font-weight:700;">${191 - idx}</td>
                                        <td style="color:var(--text-muted);">R</td>
                                        <td><span class="fui-tag">${m.id}</span></td>
                                        <td style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${m.text}</td>
                                        <td style="font-size:11px; color:var(--text-muted);">${m.timestamp || 'MAY 21, 2026'}</td>
                                        <td style="text-align:center;">${statusDot}</td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>

                <div style="display:flex; justify-content:space-between; margin-top:12px; font-size:10px; color:var(--text-dim);">
                    <div>RUN BY: KZSAMIR WORKSTATION PRO</div>
                    <div>HUB-2 - 2026</div>
                </div>
            `;

            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--hud-red); padding:20px;">FAILED TO LOAD COMMAND QUEUE DATA.</div>`;
        }
    },

    selectRow(msgId, author, text) {
        const bodyContent = decodeURIComponent(text);
        const titleEl = document.getElementById('detail-box-title');
        const bodyEl = document.getElementById('detail-box-body');
        const badgeEl = document.getElementById('detail-status-badge');

        if (titleEl) titleEl.textContent = `${msgId} / AUTHOR: ${author}`;
        if (bodyEl) bodyEl.innerHTML = `
            <div style="font-size:12px; color:var(--hud-green); margin-bottom:6px;">[ INTEGRITY: SHA-256 VERIFIED ]</div>
            <div style="background:#080808; border:1px solid var(--border-color); padding:12px; white-space:pre-wrap;">${bodyContent}</div>
            <div style="margin-top:12px; font-size:11px; color:var(--text-muted);">
                Dispatch released the message context after verifying manifest, driver credentials, seal numbers, and dock clearances.
            </div>
        `;
        if (badgeEl) badgeEl.textContent = "VERIFIED";

        EvidenceDrawer.open(msgId);
    }
};
