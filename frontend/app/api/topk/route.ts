import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json()
    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'message is required' }, { status: 400 })
    }

    const system = `You are an assistant that selects how many sources (k) to retrieve for answering a question over a set of documents.
Return only a single integer between 1 and 25 inclusive, with no extra text, punctuation, or explanation.
Guidelines:
- Short, specific questions: prefer 3-5
- Medium complexity: 5-10
- Broad comparisons, summaries, or aggregates: 10-20
- Very broad research-type queries: up to 25.`

    const completion = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-5-nano',
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: message },
      ],
      stream: false,
      temperature: 1,
      max_completion_tokens: 5,
    })

    const content = completion.choices[0]?.message?.content?.trim() || ''
    const parsed = parseInt(content, 10)
    let k = Number.isFinite(parsed) ? parsed : 5
    if (k < 1) k = 1
    if (k > 25) k = 25

    return NextResponse.json({ k })
  } catch (err) {
    console.error('topk route error', err)
    return NextResponse.json({ error: 'internal error' }, { status: 500 })
  }
}
