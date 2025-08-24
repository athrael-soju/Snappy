// frontend/lib/api/chat.ts
import { baseUrl } from '@/lib/api/client'
import { z } from 'zod'
import {
  chatRequestSchema,
  retrievedImageSchema,
  type ChatRequestSchema,
  type RetrievedImageSchema,
} from '@/lib/validation/chat'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type RetrievedImage = RetrievedImageSchema

export async function searchDocuments(query: string, k: number): Promise<RetrievedImage[]> {
  const res = await fetch(`${baseUrl}/search?q=${encodeURIComponent(query)}&k=${k}`)
  if (!res.ok) return []
  const data = await res.json()
  // Validate array of retrieved images
  const arrSchema = z.array(retrievedImageSchema)
  const parsed = arrSchema.safeParse(data)
  return parsed.success ? parsed.data : []
}

export type ChatRequest = ChatRequestSchema

export async function chatRequest(req: ChatRequest): Promise<Response> {
  // Validate outgoing payload before sending
  const parsed = chatRequestSchema.safeParse(req)
  if (!parsed.success) {
    const first = parsed.error.issues[0]
    throw new Error(`Invalid chat request: ${first?.path?.join('.') || 'payload'} ${first?.message || ''}`.trim())
  }
  return fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parsed.data),
  })
}

export async function streamAssistant(
  res: Response,
  onDelta: (chunk: string) => void
): Promise<void> {
  if (!res.ok || !res.body) {
    throw new Error(`Failed to stream chat: ${res.status}`)
  }
  // Parse Server-Sent Events from the response body
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE events are separated by a blank line \n\n
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)

      // We only care about lines starting with "data: "
      const lines = rawEvent.split('\n')
      for (const l of lines) {
        if (!l.startsWith('data: ')) continue
        const payloadStr = l.slice(6)
        try {
          const payload = JSON.parse(payloadStr)
          const eventType = payload?.event
          const data = payload?.data
          if (eventType === 'response.output_text.delta' && data?.delta) {
            onDelta(String(data.delta))
          }
        } catch {
          // ignore malformed event
        }
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
