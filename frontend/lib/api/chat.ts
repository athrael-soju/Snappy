// frontend/lib/api/chat.ts
import { baseUrl } from '@/lib/api/client'
import {
  parseKnowledgeBaseItems,
  parseSearchResults,
  type SearchItem,
} from '@/lib/api/runtime'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export async function searchDocuments(query: string, k: number): Promise<SearchItem[]> {
  const res = await fetch(`${baseUrl}/search?q=${encodeURIComponent(query)}&k=${k}`)
  if (!res.ok) return []
  const data = await res.json()
  return parseSearchResults(data)
}

export type ChatRequest = {
  message: string
  k: number
  toolCallingEnabled: boolean
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
  onDelta: (chunk: string) => void,
  onFirstChunk?: () => void,
  onKbImages?: (items: SearchItem[]) => void
): Promise<void> {
  if (!res.ok || !res.body) {
    throw new Error(`Failed to stream chat: ${res.status}`)
  }
  
  // Parse Server-Sent Events from the response body
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let firstEmitted = false
  
  while (true) {
    const { done, value } = await reader.read()
    
    if (done) {
      break
    }
    
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
            if (!firstEmitted) {
              firstEmitted = true
              onFirstChunk?.()
            }
            onDelta(String(data.delta))
          } else if (eventType === 'kb.images') {
            const items = parseKnowledgeBaseItems(data?.items)
            if (items.length > 0) {
              onKbImages?.(items)
            }
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
