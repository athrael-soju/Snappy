import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json()
    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'message is required' }, { status: 400 })
    }

    const instructions = `You are an assistant that selects how many sources (k) to retrieve for answering a question over a set of documents.
Return only a single integer between 1 and 25 inclusive, with no extra text, punctuation, or explanation.
Guidelines:
- Short, specific questions: prefer 3-5
- Medium complexity: 5-10
- Broad comparisons, summaries, or aggregates: 10-20
- Very broad research-type queries: up to 25.`

    const response = await openai.responses.create({
      model: 'gpt-5-nano',
      input: message,
      instructions,
      stream: false,
      temperature: 1,
      // max_output_tokens: 100,
      parallel_tool_calls: false,
    })

    // Responses API returns output_text as an array of segments; join for simplicity
    const content = Array.isArray((response as any).output_text)
      ? (response as any).output_text.join('').trim()
      : String((response as any).output_text ?? '').trim()
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
