// frontend/lib/hooks/use-chat.ts
'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import {
  chatRequest,
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
  const [kMode, setKMode] = useState<'auto' | 'manual'>(() => {
    if (typeof window === 'undefined') return 'manual'
    const saved = localStorage.getItem('kMode')
    return (saved === 'auto' || saved === 'manual') ? saved : 'manual'
  })
  const [model, setModel] = useState<'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano'>(() => {
    if (typeof window === 'undefined') return 'gpt-5-mini'
    const saved = localStorage.getItem('openaiModel') as 'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano' | null
    return (saved === 'gpt-5' || saved === 'gpt-5-mini' || saved === 'gpt-5-nano') ? saved : 'gpt-5-mini'
  })
  const [k, setK] = useState<number>(() => {
    if (typeof window === 'undefined') return 5
    const saved = localStorage.getItem('k')
    const parsed = saved ? parseInt(saved, 10) : NaN
    // Validate persisted value using schema bounds; fallback to default 5
    return Number.isFinite(parsed) && kSchema.safeParse(parsed).success ? parsed : 5
  })
  const [toolsEnabled, setToolsEnabled] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true
    const saved = localStorage.getItem('toolsEnabled')
    return saved === null ? true : saved === 'true'
  })
  const [imageGroups, setImageGroups] = useState<
    Array<{ url: string | null; label: string | null; score: number | null }[]>
  >([])

  // Validation schemas are imported from shared module

  // Derived validity for UI to disable send when settings are invalid
  const isSettingsValid = (() => {
    if (kMode === 'auto') return true
    return kSchema.safeParse(k).success
  })()

  // persist preferences
  useEffect(() => {
    try {
      localStorage.setItem('kMode', kMode)
      localStorage.setItem('k', String(k))
      localStorage.setItem('toolsEnabled', String(toolsEnabled))
      localStorage.setItem('openaiModel', model)
    } catch {}
  }, [kMode, k, toolsEnabled, model])


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
    const trimmedHistory: ChatMessage[] = (() => {
      const copy = [...messages]
      while (copy.length > 0) {
        const last = copy[copy.length - 1]
        if (last.role === 'assistant' && last.content.trim() === '') {
          copy.pop()
        } else {
          break
        }
      }
      return copy
    })()
    const nextHistory: ChatMessage[] = [...trimmedHistory, userMsg]
    setInput('')
    setError(null)

    // Clear citations panel; server will emit kb.images if it decides to search
    setImageGroups([])

    const basePrompt = process.env.NEXT_PUBLIC_OPENAI_SYSTEM_PROMPT ||
      "You are a helpful assistant. Be concise and accurate."

    const systemPrompt = basePrompt

    try {
      // Always stream responses
      // Make sure loading indicator is visible even when no tools are used
      setLoading(true)
      setMessages([...nextHistory, { role: 'assistant', content: '' }])
      const res = await chatRequest({
        message: text,
        systemPrompt,
        stream: true,
        model,
      })

      let assistantText = ''
      await streamAssistant(
        res,
        (delta) => {
          assistantText += delta
          setMessages((curr) => {
            if (curr.length === 0) return curr
            const updated = [...curr]
            updated[updated.length - 1] = { role: 'assistant', content: assistantText }
            return updated
          })
        },
        (evt) => {
          if (evt.event === 'kb.images' && evt.data?.images) {
            const imgs = (evt.data.images as RetrievedImage[])
            const group = imgs.map((img) => ({
              url: img.image_url ?? null,
              label: img.label ?? null,
              score: typeof img.score === 'number' ? img.score : null,
            }))
            setImageGroups([group])
          }
        }
      )
      toast.success('Response received')
    } catch (err: unknown) {
      let errorMsg = 'Streaming failed'
      if (err instanceof Error) errorMsg = err.message
      setError(errorMsg)
      toast.error('Chat Failed', { description: errorMsg })
      // Ensure the pending assistant placeholder doesn't remain empty (which would re-trigger loading animations later)
      setMessages((curr) => {
        if (curr.length === 0) return curr
        const updated = [...curr]
        const last = updated[updated.length - 1]
        if (last.role === 'assistant' && last.content.trim() === '') {
          updated[updated.length - 1] = {
            role: 'assistant',
            content: 'Sorry, I ran into an error while answering. Please try again.',
          }
        }
        return updated
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
    kMode,
    toolsEnabled,
    model,
    imageGroups,
    isSettingsValid,
    // setters
    setInput,
    setK,
    setKMode,
    setToolsEnabled,
    setModel,
    // actions
    sendMessage,
  }
}
