// frontend/lib/validation/chat.ts
import { z } from 'zod'

// Message text validation for chat input
export const messageSchema = z
  .string()
  .trim()
  .min(1, 'Please enter a question')
  .max(2000, 'Message is too long (max 2000 characters)')

// Sources (k) validation shared by UI and hook
export const kSchema = z.number().int().min(1, 'Minimum is 1').max(25, 'Maximum is 25')

export type KSchema = z.infer<typeof kSchema>

// OpenAI model selection
export const modelSchema = z.enum(['gpt-5', 'gpt-5-mini', 'gpt-5-nano'])
export type ModelSchema = z.infer<typeof modelSchema>

// Retrieved image structure from search endpoint
export const retrievedImageSchema = z.object({
  image_url: z.string().url().nullable().optional(),
  label: z.string().nullable().optional(),
  score: z.number().nullable().optional(),
})
export type RetrievedImageSchema = z.infer<typeof retrievedImageSchema>

// Chat request payload to Next.js API route
export const chatRequestSchema = z.object({
  message: messageSchema,
  systemPrompt: z.string().min(1),
  stream: z.literal(true).or(z.literal(false)),
  model: modelSchema.optional(),
})
export type ChatRequestSchema = z.infer<typeof chatRequestSchema>
