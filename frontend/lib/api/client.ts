import { OpenAPI } from '@/lib/api/generated'
import { createApiClient } from '@/lib/api/zod'

export const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

OpenAPI.BASE = baseUrl

export const zodClient = createApiClient(baseUrl)
// Optional:
// OpenAPI.WITH_CREDENTIALS = false
// OpenAPI.HEADERS = { 'X-Custom': '...' }
