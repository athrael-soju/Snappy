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
import { chooseTopK } from '@/lib/auto-topk'

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

  // very lightweight intent classifier for KB queries
  function isKbQuery(text: string): boolean {
    const q = text.toLowerCase()
    const hints = [
      'document', 'documents', 'pdf', 'page', 'pages', 'slide', 'slides',
      'knowledge base', 'knowledgebase', 'kb', 'from my files', 'in my files',
      'uploaded', 'dataset', 'report', 'contract', 'presentation', 'image search'
    ]
    // heuristic: contains any hint or asks to "find/show/search" something
    if (hints.some(h => q.includes(h))) return true
    const verbs = ['find', 'search', 'show', 'locate', 'cite', 'where in']
    return verbs.some(v => q.includes(v))
  }

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

    // Tool calling: only search when tools are enabled AND intent indicates KB query
    // Otherwise, skip search and answer directly
    let retrievedImages: RetrievedImage[] = []
    const shouldUseTool = toolsEnabled && isKbQuery(text)
    try {
      if (shouldUseTool) {
        let effectiveK = k
        if (kMode === 'auto') {
          try {
            effectiveK = await chooseTopK(text)
          } catch (err) {
            const msg = 'Failed to choose sources automatically'
            setError(msg)
            toast.error('Auto sources selection failed', { description: msg })
            return
          }
        }
        // Validate k (align with SourcesControl upper bound 25)
        const kParse = kSchema.safeParse(effectiveK)
        if (!kParse.success) {
          const msg = 'Number of sources must be between 1 and 25'
          setError(msg)
          toast.error('Invalid sources selection', { description: msg })
          return
        }

        // Only set loading after validation passes
        setLoading(true)

        const searchData = await searchDocuments(text, kParse.data)
        retrievedImages = searchData || []
        const group = retrievedImages.map((img) => ({
          url: img.image_url ?? null,
          label: img.label ?? null,
          score: typeof img.score === 'number' ? img.score : null,
        }))
        setImageGroups([group])
      } else {
        // Clear images when skipping tool to avoid stale citations panel
        setImageGroups([])
      }
    } catch (e) {
      // non-fatal
      console.warn('Image retrieval failed:', e)
    }

    const basePrompt = process.env.NEXT_PUBLIC_OPENAI_SYSTEM_PROMPT ||
      "You are a helpful assistant. Be concise and accurate."

    const kbPrompt = "You are a helpful PDF/document assistant. Use only the provided page images to answer the user's question. If the answer isn't contained in the pages, say you cannot find it. Be concise and always mention from which pages the answer is taken."

    const systemPrompt = (retrievedImages.length > 0)
      ? `${kbPrompt}

[Retrieved pages]
${retrievedImages.map((img, idx) => `Page ${idx + 1}: ${img.label || 'Unlabeled'}`).join('\n')}

Cite pages using the labels above (do not infer by result order).`
      : basePrompt

    try {
      // Always stream responses
      setMessages([...nextHistory, { role: 'assistant', content: '' }])
      const res = await chatRequest({
        message: text,
        images: retrievedImages,
        systemPrompt,
        stream: true,
        model,
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
