/* =============================================================================
   Auth Module — JWT Token Management
   ============================================================================= */
const Auth = (() => {
    const STORAGE_KEY = 'craft_tokens';
    const USER_KEY = 'craft_user';
    // Default API base URL (read fresh from localStorage each time via getApiBase)

    function getTokens() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null; }
        catch { return null; }
    }

    function setTokens(tokens) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
    }

    function getUser() {
        try { return JSON.parse(localStorage.getItem(USER_KEY)) || null; }
        catch { return null; }
    }

    function setUser(user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
    }

    function getAccessToken() {
        const t = getTokens();
        return t ? t.access : null;
    }

    function isLoggedIn() {
        return !!getAccessToken();
    }

    async function login(email, password) {
        try {
            const res = await fetch(`${getApiBase()}/accounts/login/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            // Handle both token formats: {tokens:{access,refresh}} or {access,refresh}
            const tokens = data.tokens || (data.access ? { access: data.access, refresh: data.refresh } : null);
            if (res.ok && tokens) {
                // Reject non-admin users before storing tokens
                if (data.is_staff === false) {
                    return { success: false, error: 'Access denied. This dashboard is for administrators only.' };
                }
                setTokens(tokens);
                setUser({
                    email: data.email || email,
                    full_name: data.full_name || data.first_name || email.split('@')[0],
                    is_staff: data.is_staff === true,
                    must_change_password: data.must_change_password === true
                });
                return { success: true };
            }
            // Handle various error formats
            const errMsg = data.detail || data.message || data.error
                || (data.non_field_errors && data.non_field_errors[0])
                || 'Invalid credentials';
            return { success: false, error: errMsg };
        } catch (err) {
            return { success: false, error: 'Cannot connect to server.' };
        }
    }

    async function refreshToken() {
        const tokens = getTokens();
        if (!tokens || !tokens.refresh) return false;
        try {
            const res = await fetch(`${getApiBase()}/accounts/token-refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: tokens.refresh })
            });
            if (res.ok) {
                const data = await res.json();
                setTokens({ ...tokens, access: data.access, refresh: data.refresh || tokens.refresh });
                return true;
            }
            return false;
        } catch { return false; }
    }

    function logout() {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(USER_KEY);
        window.location.href = 'index.html';
    }

    function setApiBase(url) {
        localStorage.setItem('craft_api_base', url.replace(/\/$/, ''));
    }

    function getApiBase() {
        return localStorage.getItem('craft_api_base') || 'http://127.0.0.1:8000';
    }

    return { getTokens, setTokens, getUser, setUser, getAccessToken, isLoggedIn, login, refreshToken, logout, setApiBase, getApiBase };
})();
