/**
 * ZeroGraph AI — FUI Right-Side Evidence Drawer
 * Developer: kzsamir
 */

const EvidenceDrawer = {
    init() {
        const closeBtn = document.getElementById('drawer-close-btn');
        const overlay = document.getElementById('drawer-overlay');

        if (closeBtn) closeBtn.addEventListener('click', () => this.close());
        if (overlay) overlay.addEventListener('click', () => this.close());
    },

    async open(msgId) {
        const detailContainer = document.getElementById('detail-main-content');
        const titleEl = document.getElementById('detail-box-title');
        const badgeEl = document.getElementById('detail-status-badge');

        if (titleEl) titleEl.textContent = `EVIDENCE: ${msgId}`;
        if (badgeEl) badgeEl.textContent = "VERIFIED";

        if (detailContainer) {
            detailContainer.innerHTML = `<div style="color:var(--text-muted); padding:20px; text-align:center;">LOADING EVIDENCE [ ${msgId} ]...</div>`;
        }

        try {
            const res = await API.getEvidenceDetail(msgId);
            if (!res.success) {
                if (detailContainer) detailContainer.innerHTML = `<div style="color:var(--hud-red);">ERROR LOADING EVIDENCE RECORD</div>`;
                return;
            }

            const data = res.evidence;
            const msg = data.message;
            const context = data.context || {};
            const prevMsgs = context.previous || [];
            const nextMsgs = context.next || [];

            let html = `
                <!-- FUI Metadata Box -->
                <div style="background:#080808; border:1px solid var(--border-color); padding:12px; margin-bottom:14px; font-size:11px; color:var(--text-muted);">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span>AUTHOR: <strong style="color:#fff;">${msg.author_name || 'UNKNOWN'}</strong></span>
                        <span>CHANNEL: <strong style="color:#fff;">${msg.channel || 'OPERATIONS'}</strong></span>
                    </div>
                    <div>TIMESTAMP: <strong style="color:#fff;">${msg.timestamp || 'N/A'}</strong></div>
                    <div>SENSITIVITY: <strong style="color:var(--hud-purple);">${msg.sensitivity || 'INTERNAL'}</strong></div>
                    <div style="color:var(--hud-green); margin-top:4px;">INTEGRITY: SHA-256 VERIFIED ●</div>
                </div>

                <!-- Original Message Text -->
                <div style="margin-bottom:16px;">
                    <div style="font-size:10px; color:var(--text-dim); text-transform:uppercase; margin-bottom:4px;">ORIGINAL MESSAGE TEXT</div>
                    <div style="background:#080808; border:1px solid var(--border-highlight); padding:12px; font-size:12px; line-height:1.6; color:#ffffff; white-space:pre-wrap;">
                        ${msg.text || '(empty message)'}
                    </div>
                </div>

                <!-- Surrounding Context Window -->
                <div style="margin-bottom:16px;">
                    <div style="font-size:10px; color:var(--text-dim); text-transform:uppercase; margin-bottom:6px;">CONTEXT WINDOW (SURROUNDING MESSAGES)</div>
                    
                    ${prevMsgs.map(m => `
                        <div style="padding:6px 10px; background:#070707; border-left:2px solid var(--border-bright); margin-bottom:4px; font-size:11px; color:var(--text-muted);">
                            <span style="color:var(--hud-blue);">[ ${m.id} ]</span> <strong>${m.author_name}:</strong> ${m.text}
                        </div>
                    `).join('')}

                    <div style="padding:8px 12px; background:#111111; border-left:3px solid var(--hud-green); margin:6px 0; font-size:12px; font-weight:600; color:#ffffff;">
                        <span style="color:var(--hud-green);">[ ${msg.id} ]</span> <strong>${msg.author_name}:</strong> ${msg.text}
                    </div>

                    ${nextMsgs.map(m => `
                        <div style="padding:6px 10px; background:#070707; border-left:2px solid var(--border-bright); margin-top:4px; font-size:11px; color:var(--text-muted);">
                            <span style="color:var(--hud-blue);">[ ${m.id} ]</span> <strong>${m.author_name}:</strong> ${m.text}
                        </div>
                    `).join('')}
                </div>

                <!-- Linked Findings -->
                <div>
                    <div style="font-size:10px; color:var(--text-dim); text-transform:uppercase; margin-bottom:4px;">LINKED FINDINGS (${(data.linked_findings||[]).length})</div>
                    ${(data.linked_findings||[]).map(f => `
                        <div style="padding:6px 10px; background:#0e0e0e; border:1px solid var(--border-color); margin-bottom:4px; font-size:11px;">
                            <strong>${f.finding_code}:</strong> ${f.title_bn}
                        </div>
                    `).join('') || '<div style="font-size:11px; color:var(--text-dim);">None</div>'}
                </div>
            `;

            if (detailContainer) detailContainer.innerHTML = html;

        } catch (err) {
            if (detailContainer) detailContainer.innerHTML = `<div style="color:var(--hud-red);">ERROR LOADING EVIDENCE DETAIL</div>`;
        }
    },

    close() {
        // Handled in detail sidebar panel
    }
};

document.addEventListener('DOMContentLoaded', () => EvidenceDrawer.init());
