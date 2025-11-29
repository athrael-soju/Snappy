// frontend/lib/api/chat.ts
import {
  parseKnowledgeBaseItems
} from '@/lib/api/runtime'
import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import { loadConfigFromStorage } from "@/lib/config/config-store";

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type ChatRequest = {
  message: string
  k: number
  toolCallingEnabled: boolean
  reasoning: { effort: 'minimal' | 'low' | 'medium' | 'high' }
  summary?: 'auto' | 'concise' | 'detailed' | null
  // Config flags for server-side processing
  ocrEnabled?: boolean
  duckdbEnabled?: boolean
}

export async function chatRequest(req: ChatRequest): Promise<Response> {
  const payload: Record<string, unknown> = { ...req }
  if (payload.summary === null || payload.summary === undefined) {
    delete payload.summary
  }

  // Read config from localStorage and pass to server
  // (Server doesn't have access to browser localStorage)
  if (typeof window !== 'undefined') {
    const config = loadConfigFromStorage();
    payload.ocrEnabled = config?.DEEPSEEK_OCR_ENABLED === 'True';
    payload.duckdbEnabled = config?.DUCKDB_ENABLED === 'True';
    payload.ocrIncludeImages = config?.DEEPSEEK_OCR_INCLUDE_IMAGES === 'True';
  }

  return fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
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

export type HeatmapResponse = {
  heatmap_url: string
  width: number
  height: number
}

/**
 * Fetch a heatmap for a specific image and query on-demand.
 * Returns the heatmap as a base64 data URL.
 */
export async function fetchHeatmap(
  query: string,
  imageUrl: string
): Promise<HeatmapResponse> {
  const response = await fetch('/api/search/heatmap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, image_url: imageUrl }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to fetch heatmap: ${error}`)
  }

  return response.json()
}
