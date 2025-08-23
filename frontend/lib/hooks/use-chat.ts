// frontend/lib/hooks/use-chat.ts
'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import {
  chatRequest,
  searchDocuments,
  streamAssistant,
  type RetrievedImage,
} from '@/lib/api/chat'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [k, setK] = useState<number>(5)
  const [imageGroups, setImageGroups] = useState<
    Array<{ url: string | null; label: string | null; score: number | null }[]>
  >([])

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text) return

    const userMsg: ChatMessage = { role: 'user', content: text }
    const nextHistory: ChatMessage[] = [...messages, userMsg]
    setInput('')
    setLoading(true)
    setError(null)

    // Retrieve images
    let retrievedImages: RetrievedImage[] = []
    try {
      const searchData = await searchDocuments(text, k)
      retrievedImages = searchData || []
      const group = retrievedImages.map((img) => ({
        url: img.image_url ?? null,
        label: img.label ?? null,
        score: typeof img.score === 'number' ? img.score : null,
      }))
      setImageGroups([group])
    } catch (e) {
      // non-fatal
      console.warn('Image retrieval failed:', e)
    }

    const basePrompt =
      process.env.NEXT_PUBLIC_OPENAI_SYSTEM_PROMPT ||
      "You are a helpful PDF assistant. Use only the provided page images to answer the user's question. If the answer isn't contained in the pages, say you cannot find it. Be concise and always mention from which pages the answer is taken."

    const systemPrompt = `${basePrompt}

[Retrieved pages]
${retrievedImages.map((img, idx) => `Page ${idx + 1}: ${img.label || 'Unlabeled'}`).join('\n')}

Cite pages using the labels above (do not infer by result order).`

    try {
      // Always stream responses
      setMessages([...nextHistory, { role: 'assistant', content: '' }])
      const res = await chatRequest({
        message: text,
        images: retrievedImages,
        systemPrompt,
        stream: true,
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
    imageGroups,
    // setters
    setInput,
    setK,
    // actions
    sendMessage,
  }
}
