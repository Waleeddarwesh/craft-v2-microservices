/* Modal System */
const Modal = (() => {
    function open(title, bodyHTML, footerHTML = '', cls = '') {
        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');
        content.className = `modal ${cls}`;
        content.innerHTML = `
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="btn-icon" onclick="Modal.close()" aria-label="Close">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
            <div class="modal-body">${bodyHTML}</div>
            ${footerHTML ? `<div class="modal-footer">${footerHTML}</div>` : ''}`;
        overlay.classList.add('active');
        overlay.onclick = (e) => { if (e.target === overlay) Modal.close(); };
    }

    function close() {
        document.getElementById('modal-overlay').classList.remove('active');
    }

    function confirm(title, message, onConfirm, confirmText = 'Confirm', type = 'primary') {
        window.__modalConfirmCallback = onConfirm;
        const body = `<p style="color:var(--clr-text-secondary);font-size:var(--fs-sm)">${message}</p>`;
        const footer = `<button class="btn btn-ghost" onclick="Modal.close()">Cancel</button><button class="btn btn-${type}" onclick="Modal.close(); if(window.__modalConfirmCallback) window.__modalConfirmCallback()">${confirmText}</button>`;
        open(title, body, footer);
    }

    return { open, close, confirm };
})();
