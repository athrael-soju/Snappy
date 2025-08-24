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
