/**
 * Page: Findings Register
 */
const FindingsPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">ফাাইন্ডিং ডাটা লোড হচ্ছে...</div>`;

        try {
            const res = await API.getFindings();
            const findings = res.findings || [];

            const html = `
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                        <h3 style="color:var(--accent-blue);">🔍 Audit Findings Register (${findings.length})</h3>
                        <div>
                            <span class="badge badge-purple">Human Review Required</span>
                        </div>
                    </div>

                    <div class="glass-table-container">
                        <table class="glass-table">
                            <thead>
                                <tr>
                                    <th>Code</th>
                                    <th>Title (বাংলা)</th>
                                    <th>Severity</th>
                                    <th>Confidence</th>
                                    <th>Status</th>
                                    <th>Owner</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${findings.map(f => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); color:var(--accent-blue); font-weight:700;">${f.finding_code}</td>
                                        <td><strong>${f.title_bn || f.title_en}</strong></td>
                                        <td>${Components.renderSeverityBadge(f.severity)}</td>
                                        <td style="font-family:var(--font-mono);">${Math.round((f.confidence||0.5)*100)}%</td>
                                        <td><span class="badge badge-yellow">${f.status}</span></td>
                                        <td>${f.owner_role || 'Team Lead'}</td>
                                        <td>
                                            <button class="cite-badge" onclick="FindingsPage.review('${f.id}')">
                                                Review
                                            </button>
                                        </td>
                                    </tr>
                                `).join('') || '<tr><td colspan="7" style="text-align:center;">No findings recorded.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">ফাইন্ডিং ডাটা লোড ব্যর্থ।</div>`;
        }
    },

    async review(findingId) {
        const newStatus = prompt("Enter new status (APPROVED / REJECTED / NEEDS_REVIEW / CLOSED):", "APPROVED");
        if (newStatus) {
            await API.updateFinding(findingId, { status: newStatus, reviewer_notes: "Reviewed from UI" });
            this.render();
        }
    }
};

/**
 * Page: Risk Register
 */
const RisksPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">ঝুঁকি রেজিস্টার লোড হচ্ছে...</div>`;

        try {
            const res = await API.getRisks();
            const risks = res.risks || [];

            const html = `
                <div class="glass-card">
                    <h3 style="color:var(--accent-yellow); margin-bottom:16px;">⚠️ Operational Risk Register (${risks.length})</h3>
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:20px;">
                        Risk Score = Likelihood (1-5) × Impact (1-5) × Exposure (1-5). Max Score = 125.
                    </p>

                    <div class="glass-table-container">
                        <table class="glass-table">
                            <thead>
                                <tr>
                                    <th>Risk ID</th>
                                    <th>Title</th>
                                    <th>Likelihood</th>
                                    <th>Impact</th>
                                    <th>Exposure</th>
                                    <th>Score</th>
                                    <th>Band</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${risks.map(r => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); color:var(--accent-yellow);">${r.risk_id}</td>
                                        <td><strong>${r.title}</strong></td>
                                        <td style="font-family:var(--font-mono);">${r.likelihood}</td>
                                        <td style="font-family:var(--font-mono);">${r.impact}</td>
                                        <td style="font-family:var(--font-mono);">${r.exposure}</td>
                                        <td style="font-family:var(--font-mono); font-weight:800; color:var(--accent-orange);">${r.score}</td>
                                        <td>${Components.renderSeverityBadge(r.band)}</td>
                                        <td><span class="badge badge-yellow">${r.status}</span></td>
                                    </tr>
                                `).join('') || '<tr><td colspan="8" style="text-align:center;">No active risk records.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">ঝুঁকি রেজিস্টার লোড ব্যর্থ।</div>`;
        }
    }
};

/**
 * Page: Action Register
 */
const ActionsPage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">অ্যাকশন রেজিস্টার লোড হচ্ছে...</div>`;

        try {
            const res = await API.getActions();
            const actions = res.actions || [];

            const html = `
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                        <h3 style="color:var(--accent-green);">✅ Corrective Action Register (${actions.length})</h3>
                        <button class="btn-primary" onclick="ActionsPage.createPrompt()" style="padding:6px 14px; font-size:0.85rem;">
                            + New Action Item
                        </button>
                    </div>

                    <div class="glass-table-container">
                        <table class="glass-table">
                            <thead>
                                <tr>
                                    <th>Action Code</th>
                                    <th>Action Title (বাংলা)</th>
                                    <th>Owner Role</th>
                                    <th>Priority</th>
                                    <th>Due Date</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${actions.map(a => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); color:var(--accent-green); font-weight:700;">${a.action_code}</td>
                                        <td><strong>${a.title_bn}</strong></td>
                                        <td>${a.owner_role || 'Team Lead'}</td>
                                        <td><span class="badge badge-orange">${a.priority || 'P2'}</span></td>
                                        <td style="font-size:0.85rem;">${a.suggested_due_date || '7 days'}</td>
                                        <td><span class="badge ${a.status === 'COMPLETED' ? 'badge-green' : 'badge-yellow'}">${a.status}</span></td>
                                        <td>
                                            <button class="cite-badge" onclick="ActionsPage.toggleStatus('${a.id}', '${a.status}')">
                                                ${a.status === 'COMPLETED' ? 'Reopen' : 'Mark Complete'}
                                            </button>
                                        </td>
                                    </tr>
                                `).join('') || '<tr><td colspan="7" style="text-align:center;">No actions recorded.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">অ্যাকশন রেজিস্টার লোড ব্যর্থ।</div>`;
        }
    },

    async toggleStatus(actionId, currentStatus) {
        const nextStatus = currentStatus === 'COMPLETED' ? 'OPEN' : 'COMPLETED';
        await API.updateAction(actionId, { status: nextStatus });
        this.render();
    },

    async createPrompt() {
        const title = prompt("Enter Action Title (Bengali):");
        if (title) {
            await fetch('/api/actions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title_bn: title, owner_role: 'Team Lead', priority: 'P2' })
            });
            this.render();
        }
    }
};

/**
 * Page: Evidence Explorer
 */
const EvidencePage = {
    async render() {
        const container = document.getElementById('page-content');
        container.innerHTML = `<div style="text-align:center; padding:40px;">ইভিডেন্স ডাটাবেস লোড হচ্ছে...</div>`;

        try {
            const res = await API.getMessages({ limit: 50 });
            const messages = res.messages || [];

            const html = `
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                        <h3 style="color:var(--accent-blue);">📁 Evidence Explorer (6,914 Local Records)</h3>
                        <input type="text" id="ev-search-input" class="form-input" placeholder="Search evidence text or ID..." style="width:300px;" onkeyup="EvidencePage.search(event)">
                    </div>

                    <div class="glass-table-container">
                        <table class="glass-table">
                            <thead>
                                <tr>
                                    <th>Message ID</th>
                                    <th>Timestamp</th>
                                    <th>Speaker</th>
                                    <th>Message Snippet</th>
                                    <th>Sensitivity</th>
                                    <th>Inspect</th>
                                </tr>
                            </thead>
                            <tbody id="ev-table-body">
                                ${messages.map(m => `
                                    <tr>
                                        <td style="font-family:var(--font-mono); color:var(--accent-blue);">${m.id}</td>
                                        <td style="font-family:var(--font-mono); font-size:0.8rem;">${m.timestamp || 'N/A'}</td>
                                        <td><strong>${m.author_name}</strong></td>
                                        <td style="max-width:350px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${m.text}</td>
                                        <td><span class="badge badge-purple">${m.sensitivity || 'INTERNAL'}</span></td>
                                        <td>${Components.renderEvidenceChip(m.id)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } catch (err) {
            container.innerHTML = `<div style="color:var(--accent-red); padding:20px;">ইভিডেন্স এক্সপ্লোরার লোড ব্যর্থ।</div>`;
        }
    },

    async search(e) {
        if (e.key === 'Enter' || e.type === 'keyup') {
            const q = document.getElementById('ev-search-input').value.trim();
            const res = await API.getMessages({ q, limit: 50 });
            const tbody = document.getElementById('ev-table-body');
            tbody.innerHTML = (res.messages || []).map(m => `
                <tr>
                    <td style="font-family:var(--font-mono); color:var(--accent-blue);">${m.id}</td>
                    <td style="font-family:var(--font-mono); font-size:0.8rem;">${m.timestamp || 'N/A'}</td>
                    <td><strong>${m.author_name}</strong></td>
                    <td style="max-width:350px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${m.text}</td>
                    <td><span class="badge badge-purple">${m.sensitivity || 'INTERNAL'}</span></td>
                    <td>${Components.renderEvidenceChip(m.id)}</td>
                </tr>
            `).join('') || '<tr><td colspan="6" style="text-align:center;">No matching messages found.</td></tr>';
        }
    }
};
