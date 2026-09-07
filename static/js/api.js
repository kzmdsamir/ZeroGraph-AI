/**
 * ZeroGraph AI — API Client Wrapper
 * Handles air-gapped requests to local backend API routes.
 * Developer: kzsamir
 */

const API = {
    async analyze(payload) {
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await resp.json();
    },

    async getSystemHealth() {
        const resp = await fetch('/api/system-health');
        return await resp.json();
    },

    async getDataQuality() {
        const resp = await fetch('/api/data-quality');
        return await resp.json();
    },

    async getFindings(filters = {}) {
        const query = new URLSearchParams(filters).toString();
        const resp = await fetch(`/api/findings?${query}`);
        return await resp.json();
    },

    async getFindingDetail(id) {
        const resp = await fetch(`/api/findings/${id}`);
        return await resp.json();
    },

    async updateFinding(id, payload) {
        const resp = await fetch(`/api/findings/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await resp.json();
    },

    async getRisks() {
        const resp = await fetch('/api/risks');
        return await resp.json();
    },

    async getActions(filters = {}) {
        const query = new URLSearchParams(filters).toString();
        const resp = await fetch(`/api/actions?${query}`);
        return await resp.json();
    },

    async updateAction(id, payload) {
        const resp = await fetch(`/api/actions/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await resp.json();
    },

    async getMessages(params = {}) {
        const query = new URLSearchParams(params).toString();
        const resp = await fetch(`/api/messages?${query}`);
        return await resp.json();
    },

    async getEvidenceDetail(id) {
        const resp = await fetch(`/api/evidence/${id}`);
        return await resp.json();
    },

    async getAnalysisRuns() {
        const resp = await fetch('/api/analysis-runs');
        return await resp.json();
    },

    async verifyRunIntegrity(id) {
        const resp = await fetch(`/api/analysis-runs/${id}/verify-integrity`, { method: 'POST' });
        return await resp.json();
    },

    async getSettings() {
        const resp = await fetch('/api/settings');
        return await resp.json();
    }
};
