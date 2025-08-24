// frontend/lib/auto-topk.ts
import { kSchema } from '@/lib/validation/chat'

export async function chooseTopK(message: string): Promise<number> {
  const res = await fetch('/api/topk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) {
    throw new Error(`TopK selection failed: ${res.status}`)
  }
  const data = await res.json()
  const k = Number(data?.k)
  const parsed = kSchema.safeParse(k)
  if (!parsed.success) {
    throw new Error('Model returned invalid k')
  }
  return parsed.data
}
