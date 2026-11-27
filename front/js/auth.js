(function () {
    const configuredBase = window.API_BASE_URL || localStorage.getItem('apiBaseUrl');
    const defaultHost = window.location.hostname || 'localhost';
    const baseUrl = (configuredBase || `http://${defaultHost}:8000/api/v1`).replace(/\/$/, '');

    async function request(path, options = {}) {
        const response = await fetch(`${baseUrl}${path}`, {
            ...options,
            credentials: 'include',
            headers: {
                ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
                ...(options.headers || {}),
            },
        });

        if (!response.ok) {
            let message = `Ошибка запроса (${response.status})`;
            try {
                const data = await response.json();
                message = data.detail || data.msg || message;
            } catch (_) {
                // Ответ может быть не JSON.
            }
            const error = new Error(message);
            error.status = response.status;
            throw error;
        }

        if (response.status === 204) return null;
        const contentType = response.headers.get('content-type') || '';
        return contentType.includes('application/json') ? response.json() : response;
    }

    window.api = {
        baseUrl,
        get: (path) => request(path),
        post: (path, body) => request(path, {
            method: 'POST',
            body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
        }),
        put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
        patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body ?? {}) }),
        delete: (path) => request(path, { method: 'DELETE' }),
        download: async (path, filename) => {
            const response = await request(path);
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
            URL.revokeObjectURL(url);
        },
    };
})();
