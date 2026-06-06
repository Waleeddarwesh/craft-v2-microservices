/* Keyboard Shortcuts Manager */
const ShortcutsManager = (() => {
    let active = true;

    function init() {
        document.addEventListener('keydown', handleKeydown);
    }

    function handleKeydown(e) {
        if (!active) return;
        
        // Ignore if focus is in an input or textarea (except for global shortcuts that might want to override)
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
            // Escape to blur search
            if (e.key === 'Escape') {
                document.activeElement.blur();
                const sr = document.getElementById('search-results');
                if (sr) sr.style.display = 'none';
            }
            return;
        }

        // Search focus (Ctrl+K or /)
        if ((e.ctrlKey && e.key === 'k') || e.key === '/') {
            e.preventDefault();
            document.getElementById('global-search')?.focus();
            return;
        }

        // Global key sequences (g then [key])
        if (e.key === 'g') {
            // Wait for next key
            const nextKey = (ev) => {
                if (ev.key === 'o') Router.navigate('#orders');
                if (ev.key === 'p') Router.navigate('#products');
                if (ev.key === 'u') Router.navigate('#users');
                if (ev.key === 'd') Router.navigate('#overview');
                document.removeEventListener('keydown', nextKey);
            };
            document.addEventListener('keydown', nextKey);
            // Cancel sequence after 1s
            setTimeout(() => { document.removeEventListener('keydown', nextKey); }, 1000);
            return;
        }

        // Show cheatsheet
        if (e.key === '?') {
            showCheatsheet();
        }
    }

    function showCheatsheet() {
        const html = `
            <div style="display:grid; gap:var(--space-2)">
                <div style="display:flex; justify-content:space-between; padding:var(--space-2) 0; border-bottom:1px solid var(--clr-surface-border)">
                    <span>Focus Search</span>
                    <kbd style="font-family:var(--font-mono); background:var(--clr-bg); padding:2px 6px; border-radius:4px; border:1px solid var(--clr-surface-border)">Ctrl + K</kbd> or <kbd style="font-family:var(--font-mono); background:var(--clr-bg); padding:2px 6px; border-radius:4px; border:1px solid var(--clr-surface-border)">/</kbd>
                </div>
                <div style="display:flex; justify-content:space-between; padding:var(--space-2) 0; border-bottom:1px solid var(--clr-surface-border)">
                    <span>Go to Dashboard</span>
                    <span><kbd>g</kbd> then <kbd>d</kbd></span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:var(--space-2) 0; border-bottom:1px solid var(--clr-surface-border)">
                    <span>Go to Orders</span>
                    <span><kbd>g</kbd> then <kbd>o</kbd></span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:var(--space-2) 0; border-bottom:1px solid var(--clr-surface-border)">
                    <span>Go to Products</span>
                    <span><kbd>g</kbd> then <kbd>p</kbd></span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:var(--space-2) 0; border-bottom:1px solid var(--clr-surface-border)">
                    <span>Go to Users</span>
                    <span><kbd>g</kbd> then <kbd>u</kbd></span>
                </div>
            </div>
            <style>kbd { font-family:var(--font-mono); background:var(--clr-bg); padding:2px 6px; border-radius:4px; border:1px solid var(--clr-surface-border); font-size:var(--fs-xs); }</style>
        `;
        Modal.open('Keyboard Shortcuts', html);
    }

    return { init };
})();
