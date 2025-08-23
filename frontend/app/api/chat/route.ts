import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { message, images, systemPrompt } = await request.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Build Responses API input with proper content part types
    const userContent: Array<any> = [
      { type: 'input_text', text: message },
    ]

    // Convert images to base64 data URLs since OpenAI can't access localhost
    if (images && images.length > 0) {
      for (const image of images) {
        if (image.image_url) {
          try {
            const imageResponse = await fetch(image.image_url)
            if (imageResponse.ok) {
              const imageBuffer = await imageResponse.arrayBuffer()
              const base64 = Buffer.from(imageBuffer).toString('base64')
              const mimeType = imageResponse.headers.get('content-type') || 'image/jpeg'
              const dataUrl = `data:${mimeType};base64,${base64}`

              userContent.push({
                type: 'input_image',
                image_url: dataUrl,
              })
            } else {
              console.warn(`Failed to fetch image: ${image.image_url} - ${imageResponse.status}`)
            }
          } catch (error) {
            console.warn(`Error fetching image: ${image.image_url}`, error)
          }
        }
      }
    }

    // Always stream using the Responses API
    const events = await openai.responses.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      // Responses API input is an array of turns
      input: [
        {
          role: 'user',
          content: userContent,
        },
      ] as any,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
      max_output_tokens: parseInt(process.env.OPENAI_MAX_TOKENS || '1500'),
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
