// frontend/lib/hooks/use-chat.ts
'use client'

import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  chatRequest,
  streamAssistant,
} from '@/lib/api/chat'
import { kSchema, messageSchema } from '@/lib/validation/chat'

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [timeToFirstTokenMs, setTimeToFirstTokenMs] = useState<number | null>(null)
  const [k, setK] = useState<number>(() => {
    if (typeof window === 'undefined') return 5
    const saved = localStorage.getItem('k')
    const parsed = saved ? parseInt(saved, 10) : NaN
    // Validate persisted value using schema bounds; fallback to default 5
    return Number.isFinite(parsed) && kSchema.safeParse(parsed).success ? parsed : 5
  })
  const [toolCallingEnabled, setToolCallingEnabled] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true
    try {
      const saved = localStorage.getItem('tool-calling-enabled')
      if (saved === null) return true
      return saved === 'true'
    } catch {
      return true
    }
  })
  const [imageGroups, setImageGroups] = useState<
    Array<{ url: string | null; label: string | null; score: number | null }>[
    ]>([])
  // Keep all images keyed by assistant message id to avoid mixing across turns
  const imagesByMessageRef = useRef<Record<string, Array<{ url: string | null; label: string | null; score: number | null }>>>({})
  const currentAssistantIdRef = useRef<string | null>(null)

  const genId = () =>
    (typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? (crypto as any).randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`)

  // Validation schemas are imported from shared module

  // Derived validity for UI to disable send when settings are invalid
  const isSettingsValid = kSchema.safeParse(k).success

  // persist preferences
  useEffect(() => {
    try {
      localStorage.setItem('k', String(k))
    } catch { }
  }, [k])

  useEffect(() => {
    try {
      localStorage.setItem('tool-calling-enabled', String(toolCallingEnabled))
    } catch { }
  }, [toolCallingEnabled])

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()

    // Validate message
    const msgParse = messageSchema.safeParse(text)
    if (!msgParse.success) {
      const msg = msgParse.error.issues[0]?.message ?? 'Invalid input'
      setError(msg)
      toast.error('Invalid question', { description: msg })
      return
    }

    const userMsg: ChatMessage = { id: genId(), role: 'user', content: text }
    const nextHistory: ChatMessage[] = [...messages, userMsg]
    setInput('')
    setError(null)
    // reset previous visual citations for new request
    setImageGroups([])
    // Reset current assistant association
    currentAssistantIdRef.current = null
    // Mark as loading so UI shows thinking bubble until first token arrives
    setLoading(true)
    setTimeToFirstTokenMs(null)

    try {
      const start = performance.now()
      const assistantId = genId()
      currentAssistantIdRef.current = assistantId
      setMessages([...nextHistory, { id: assistantId, role: 'assistant', content: '' }])
      const res = await chatRequest({
        message: text,
        k: k,
        toolCallingEnabled,
      })

      let assistantText = ''

      await streamAssistant(res, (delta) => {
        assistantText += delta
        setMessages((curr) => {
          if (curr.length === 0) return curr
          const updated = [...curr]
          // Preserve the assistant message id while updating content
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: assistantText,
          }
          return updated
        })
      }, () => {
        // first streamed token has arrived
        setTimeToFirstTokenMs(performance.now() - start)
      }, (items) => {
        // Populate from SSE regardless of tool setting; server only emits when images are actually used
        const mapped = (Array.isArray(items) ? items : []).map((it) => ({
          url: (it as any).image_url ?? null,
          label: (it as any).label ?? null,
          score: typeof (it as any).score === 'number' ? (it as any).score : null,
        }))
        if (mapped.length > 0) {
          const msgId = currentAssistantIdRef.current
          if (!msgId) {
            // No assistant context; ignore defensively
            return
          }
          const prev = imagesByMessageRef.current[msgId] || []
          // append + dedupe by url
          const combined = [...prev, ...mapped]
          const seen = new Set<string>()
          const deduped: Array<{ url: string | null; label: string | null; score: number | null }> = []
          for (const it of combined) {
            const key = it.url || ''
            if (key && !seen.has(key)) {
              seen.add(key)
              deduped.push(it)
            }
          }
          imagesByMessageRef.current[msgId] = deduped
          // Expose only the current assistant turn's images to the UI
          setImageGroups([deduped])
        }
      })
      
    } catch (err: unknown) {
      let errorMsg = 'Streaming failed'
      if (err instanceof Error) errorMsg = err.message
      setError(errorMsg)
      toast.error('Chat Failed', { description: errorMsg })
      // Remove the assistant placeholder message that was added before streaming
      // to avoid showing a lingering loading bubble on the next message
      setMessages((curr) => {
        if (curr.length === 0) return curr
        const last = curr[curr.length - 1]
        if (last.role === 'assistant' && last.content === '') {
          return curr.slice(0, -1)
        }
        return curr
      })
    } finally {
      setLoading(false)
    }
  }

  return {
    // state
    input,
    messages,
    loading,
    error,
    timeToFirstTokenMs,
    k,
    toolCallingEnabled,
    imageGroups,
    isSettingsValid,
    // setters
    setInput,
    setK,
    setToolCallingEnabled,
    // actions
    sendMessage,
  }
}
