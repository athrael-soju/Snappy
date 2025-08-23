// frontend/lib/api/chat.ts
import { baseUrl } from '@/lib/api/client'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type RetrievedImage = {
  image_url?: string | null
  label?: string | null
  score?: number | null
}

export async function searchDocuments(query: string, k: number): Promise<RetrievedImage[]> {
  const res = await fetch(`${baseUrl}/search?q=${encodeURIComponent(query)}&k=${k}`)
  if (!res.ok) return []
  const data = await res.json()
  return Array.isArray(data) ? data : []
}

export type ChatRequest = {
  message: string
  images: RetrievedImage[]
  systemPrompt: string
  stream: boolean
}

export async function chatRequest(req: ChatRequest): Promise<Response> {
  return fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function streamAssistant(
  res: Response,
  onDelta: (chunk: string) => void
): Promise<void> {
  if (!res.ok || !res.body) {
    throw new Error(`Failed to stream chat: ${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n').filter((l) => l.trim())
    for (const line of lines) {
      try {
        const parsed = JSON.parse(line)
        if (parsed.content) onDelta(parsed.content as string)
      } catch (_) {
        // ignore
      }
    }
  }
}

export async function readFullAssistant(res: Response): Promise<string> {
  if (!res.ok || !res.body) {
    throw new Error(`Chat failed: ${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let full = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n').filter((l) => l.trim())
    for (const line of lines) {
      try {
        const parsed = JSON.parse(line)
        if (parsed.content) full += parsed.content as string
      } catch (_) {
        // ignore
      }
    }
  }
  return full
}
