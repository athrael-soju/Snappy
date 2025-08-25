// frontend/lib/hooks/use-chat.ts
'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import {
  chatRequest,
  searchDocuments,
  streamAssistant,
  type RetrievedImage,
} from '@/lib/api/chat'
import { kSchema, messageSchema } from '@/lib/validation/chat'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [k, setK] = useState<number>(() => {
    if (typeof window === 'undefined') return 5
    const saved = localStorage.getItem('k')
    const parsed = saved ? parseInt(saved, 10) : NaN
    // Validate persisted value using schema bounds; fallback to default 5
    return Number.isFinite(parsed) && kSchema.safeParse(parsed).success ? parsed : 5
  })
  const [imageGroups, setImageGroups] = useState<
    Array<{ url: string | null; label: string | null; score: number | null }>[
    ]>([])

  // Validation schemas are imported from shared module

  // Derived validity for UI to disable send when settings are invalid
  const isSettingsValid = kSchema.safeParse(k).success

  // persist preferences
  useEffect(() => {
    try {
      localStorage.setItem('k', String(k))
    } catch { }
  }, [k])

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

    const userMsg: ChatMessage = { role: 'user', content: text }
    const nextHistory: ChatMessage[] = [...messages, userMsg]
    setInput('')
    setError(null)

    try {
      setMessages([...nextHistory, { role: 'assistant', content: '' }])
      const res = await chatRequest({
        message: text,
        k: k
      })

      let assistantText = ''
      await streamAssistant(res, (delta) => {
        assistantText += delta
        setMessages((curr) => {
          if (curr.length === 0) return curr
          const updated = [...curr]
          updated[updated.length - 1] = { role: 'assistant', content: assistantText }
          return updated
        })
      })
      toast.success('Response received')
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
    k,
    imageGroups,
    isSettingsValid,
    // setters
    setInput,
    setK,
    // actions
    sendMessage,
  }
}
