// frontend/lib/api/client.ts
import { OpenAPI } from '@/lib/api/generated'

export const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

OpenAPI.BASE = baseUrl
// Optional:
// OpenAPI.WITH_CREDENTIALS = false
// OpenAPI.HEADERS = { 'X-Custom': '...' }