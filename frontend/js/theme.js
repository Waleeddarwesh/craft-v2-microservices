/* Theme Manager — Dark/Light Mode Toggle with localStorage persistence */
const ThemeManager = (() => {
    const STORAGE_KEY = 'craft_theme';

    const ICONS = {
        sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
        moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
    };

    function getTheme() {
        return localStorage.getItem(STORAGE_KEY) || 'dark';
    }

    function setTheme(theme) {
        // Add smooth transition class
        document.documentElement.classList.add('theme-transition');

        // Apply theme
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);

        // Update toggle button icon
        updateToggleIcon(theme);

        // Remove transition class after animation completes
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transition');
        }, 400);
    }

    function toggle() {
        const current = getTheme();
        setTheme(current === 'dark' ? 'light' : 'dark');
    }

    function updateToggleIcon(theme) {
        const btn = document.getElementById('theme-toggle-btn');
        if (btn) {
            btn.innerHTML = theme === 'dark' ? ICONS.sun : ICONS.moon;
            btn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        }
    }

    /** Call on page load to apply saved theme instantly (no flash) */
    function init() {
        const theme = getTheme();
        document.documentElement.setAttribute('data-theme', theme);
    }

    return { init, toggle, getTheme, setTheme, updateToggleIcon, ICONS };
})();
