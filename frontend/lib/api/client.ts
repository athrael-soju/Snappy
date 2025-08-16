import createClient from 'openapi-fetch'
import type { paths } from './schema'

// Use your backend URL (expose via Next public env)
const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export const api = createClient<paths>({ baseUrl })