/**
 * INDUSTRIAL API CLIENT
 * 
 * Type-safe API client for backend communication.
 * Features:
 * - Fetch-based (no external dependencies)
 * - Request/response interceptors
 * - Error handling with typed errors
 * - Base URL configuration
 */

// Environment configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let currentTenantId: string | null = null;

export const setTenantId = (id: string | null) => {
    currentTenantId = id;
};

export const getTenantId = () => currentTenantId;

/**
 * API Error with detailed information
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        public statusText: string,
        public data: unknown,
        public requestId?: string
    ) {
        super(`API Error: ${status} ${statusText}`);
        this.name = "ApiError";
    }
}

/**
 * Request configuration
 */
interface RequestConfig extends RequestInit {
    params?: Record<string, string | number | boolean | undefined>;
}

/**
 * Build URL with query parameters
 */
function buildUrl(path: string, params?: RequestConfig["params"]): string {
    const url = new URL(path, API_BASE_URL);

    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) {
                url.searchParams.append(key, String(value));
            }
        });
    }

    return url.toString();
}

/**
 * Core fetch wrapper with error handling
 */
async function request<T>(
    path: string,
    config: RequestConfig = {}
): Promise<T> {
    const { params, ...fetchConfig } = config;

    const url = buildUrl(path, params);

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...((fetchConfig.headers as Record<string, string>) || {}),
    };

    if (currentTenantId) {
        headers["X-Tenant-ID"] = currentTenantId;
    }

    const response = await fetch(url, {
        ...fetchConfig,
        headers,
    });

    // Handle error responses
    if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new ApiError(
            response.status,
            response.statusText,
            data,
            response.headers.get("X-Request-ID") || undefined
        );
    }

    // Handle empty responses
    if (response.status === 204) {
        return undefined as T;
    }

    return response.json();
}

/**
 * HTTP method helpers
 */
export const api = {
    get: <T>(path: string, config?: RequestConfig) =>
        request<T>(path, { ...config, method: "GET" }),

    post: <T>(path: string, data?: unknown, config?: RequestConfig) =>
        request<T>(path, {
            ...config,
            method: "POST",
            body: data ? JSON.stringify(data) : undefined,
        }),

    put: <T>(path: string, data?: unknown, config?: RequestConfig) =>
        request<T>(path, {
            ...config,
            method: "PUT",
            body: data ? JSON.stringify(data) : undefined,
        }),

    patch: <T>(path: string, data?: unknown, config?: RequestConfig) =>
        request<T>(path, {
            ...config,
            method: "PATCH",
            body: data ? JSON.stringify(data) : undefined,
        }),

    delete: <T>(path: string, config?: RequestConfig) =>
        request<T>(path, { ...config, method: "DELETE" }),
};

export { API_BASE_URL };
