const ApiDocsPage = (() => {
    async function render(container) {
        container.innerHTML = `
            <div class="page-header">
                <div><h1></h1><p></p></div>
            </div>
            <div class="card p-0" style="min-height: 80vh; background: white;">
                <div id="swagger-ui"></div>
            </div>
        `;

        if (!document.getElementById('swagger-ui-css')) {
            const link = document.createElement('link');
            link.id = 'swagger-ui-css';
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css';
            document.head.appendChild(link);
        }

        if (!document.getElementById('swagger-ui-custom-css')) {
            const style = document.createElement('style');
            style.id = 'swagger-ui-custom-css';
            style.innerHTML = `
                .swagger-ui .wrapper { padding: 0; max-width: 100%; }
                .swagger-ui .info { margin: 20px 0; }
                .swagger-ui .scheme-container { background: transparent; padding: 10px 0; margin-bottom: 20px; box-shadow: none; border-bottom: 1px solid var(--clr-surface-border); }
            `;
            document.head.appendChild(style);
        }

        if (!window.SwaggerUIBundle) {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js';
            script.onload = initSwagger;
            document.body.appendChild(script);
        } else {
            initSwagger();
        }
    }

    function initSwagger() {
        const token = Auth.getTokens()?.access;
        const apiBase = Auth.getApiBase ? Auth.getApiBase() : window.location.origin;

        window.ui = SwaggerUIBundle({
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset || []
            ],
            urls: [
                { url: apiBase + "/docs/?format=openapi", name: "Admin API" },
                { url: apiBase + "/product/api/schema/", name: "Catalog API" },
                { url: apiBase + "/orders/api/schema/", name: "Orders API" },
                { url: apiBase + "/payment/api/schema/", name: "Payments API" },
                { url: apiBase + "/review/api/schema/", name: "Platform API" },
                { url: apiBase + "/reports/api/schema/", name: "Reporting API" }
            ],
            requestInterceptor: (req) => {
                if (token) {
                    req.headers.Authorization = 'Bearer ' + token;
                }
                return req;
            }
        });
    }

    return { render };
})();