import { OpenAPI } from '@/lib/api/generated'

/**
 * Get the appropriate API base URL depending on execution context
 * - Server-side (Node.js): Use internal Docker service name or API_BASE_URL_INTERNAL
 * - Client-side (Browser): Use NEXT_PUBLIC_API_BASE_URL for browser requests
 */
function getApiBaseUrl(): string {
    // Server-side (Node.js) - inside Docker or server environment
    if (typeof window === 'undefined') {
        // Use internal Docker service name or fallback to NEXT_PUBLIC_ for development
        return process.env.API_BASE_URL_INTERNAL
            ?? process.env.NEXT_PUBLIC_API_BASE_URL
            ?? 'http://localhost:8000';
    }

    // Client-side (Browser)
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
}

export const baseUrl = getApiBaseUrl()

OpenAPI.BASE = baseUrl
// Optional:
// OpenAPI.WITH_CREDENTIALS = false
// OpenAPI.HEADERS = { 'X-Custom': '...' }