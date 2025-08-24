import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { message, images, systemPrompt, model } = await request.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Build Responses API input with proper content part types
    const userContent: Array<any> = [
      { type: 'input_text', text: message },
    ]

    // Prefer sending public HTTPS image URLs directly. Fallback to data URL for localhost/private URLs.
    if (images && images.length > 0) {
      for (const image of images) {
        const url = image.image_url?.toString() || ''
        if (!url) continue
        const isHttp = url.startsWith('http://') || url.startsWith('https://')
        const isLocal = /(^http:\/\/localhost)|(^http:\/\/127\.0\.0\.1)|(^https:\/\/localhost)|(^https:\/\/127\.0\.0\.1)/.test(url)

        if (isHttp && !isLocal) {
          // Publicly reachable URL – send as-is
          userContent.push({ type: 'input_image', image_url: url })
        } else {
          // Private/localhost – inline as data URL
          try {
            const imageResponse = await fetch(url)
            if (imageResponse.ok) {
              const imageBuffer = await imageResponse.arrayBuffer()
              const base64 = Buffer.from(imageBuffer).toString('base64')
              const mimeType = imageResponse.headers.get('content-type') || 'image/jpeg'
              const dataUrl = `data:${mimeType};base64,${base64}`
              userContent.push({ type: 'input_image', image_url: dataUrl })
            } else {
              console.warn(`Failed to fetch image: ${url} - ${imageResponse.status}`)
            }
          } catch (error) {
            console.warn(`Error fetching image: ${url}`, error)
          }
        }
      }
    }

    // Always stream using the Responses API
    const events = await openai.responses.create({
      model: model || 'gpt-5-nano',
      // Responses API input is an array of turns
      input: [
        {
          role: 'user',
          content: userContent,
        },
      ] as any,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
      // max_output_tokens: parseInt(process.env.OPENAI_MAX_TOKENS || '1500'),
      stream: true,
      parallel_tool_calls: false,
      instructions: systemPrompt || undefined,
    });

    const encoder = new TextEncoder();
    const readableStream = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          for await (const event of events as any) {
            // Send all events as SSE lines to match starter app
            const payload = JSON.stringify({ event: event.type, data: event });
            controller.enqueue(encoder.encode(`data: ${payload}\n\n`));
          }
          controller.close();
        } catch (error) {
          console.error('Stream error:', error);
          controller.error(error);
        }
      },
    });

    return new Response(readableStream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
