/* =============================================================================
   API Client — Fetch Wrapper with JWT Auth
   ============================================================================= */
const API = (() => {
    function getBase() { return Auth.getApiBase(); }

    async function request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${getBase()}${endpoint}`;
        const headers = { ...options.headers };
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = headers['Content-Type'] || 'application/json';
        }
        const token = Auth.getAccessToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (window.I18n) headers['Accept-Language'] = window.I18n.getLang();

        let res;
        try {
            res = await fetch(url, { ...options, headers });
        } catch (err) {
            throw new Error('Network error — cannot reach server.');
        }

        // Token expired, try refresh
        if (res.status === 401) {
            const refreshed = await Auth.refreshToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${Auth.getAccessToken()}`;
                res = await fetch(url, { ...options, headers });
            } else {
                Auth.logout();
                return;
            }
        }

        if (res.status === 204) return null;

        const data = await res.json().catch(() => null);
        if (!res.ok) {
            const msg = data?.detail || data?.message || data?.error || `Request failed (${res.status})`;
            throw new Error(msg);
        }
        return data;
    }

    const get = (ep, params) => {
        let url = ep;
        if (params) {
            const qs = new URLSearchParams();
            Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '' && v !== null) qs.set(k, v); });
            const s = qs.toString();
            if (s) url += (url.includes('?') ? '&' : '?') + s;
        }
        return request(url, { method: 'GET' });
    };
    const post = (ep, body) => request(ep, { method: 'POST', body: JSON.stringify(body) });
    const patch = (ep, body) => request(ep, { method: 'PATCH', body: JSON.stringify(body) });
    const put = (ep, body) => request(ep, { method: 'PUT', body: JSON.stringify(body) });
    const del = (ep) => request(ep, { method: 'DELETE' });

    return { get, post, patch, put, del, request };
})();
