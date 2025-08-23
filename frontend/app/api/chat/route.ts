import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { message, images, systemPrompt, stream: enableStream = true } = await request.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Prepare messages for OpenAI
    const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [];

    // Add system prompt
    if (systemPrompt) {
      messages.push({
        role: 'system',
        content: systemPrompt,
      });
    }

    // Add user message with images if provided
    if (images && images.length > 0) {
      const content: OpenAI.Chat.Completions.ChatCompletionContentPart[] = [
        {
          type: 'text',
          text: message,
        },
      ];

      // Convert images to base64 data URLs since OpenAI can't access localhost
      for (const image of images) {
        if (image.image_url) {
          try {
            // Fetch image from MinIO
            const imageResponse = await fetch(image.image_url);
            if (imageResponse.ok) {
              const imageBuffer = await imageResponse.arrayBuffer();
              const base64 = Buffer.from(imageBuffer).toString('base64');
              const mimeType = imageResponse.headers.get('content-type') || 'image/jpeg';
              const dataUrl = `data:${mimeType};base64,${base64}`;

              content.push({
                type: 'image_url',
                image_url: {
                  url: dataUrl,
                  detail: 'low',
                },
              });
            } else {
              console.warn(`Failed to fetch image: ${image.image_url} - ${imageResponse.status}`);
            }
          } catch (error) {
            console.warn(`Error fetching image: ${image.image_url}`, error);
          }
        }
      }

      messages.push({
        role: 'user',
        content,
      });
    } else {
      messages.push({
        role: 'user',
        content: message,
      });
    }

    // Create OpenAI response (streaming or non-streaming based on request)
    const response = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-5-nano',
      messages,
      stream: enableStream,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
      max_completion_tokens: parseInt(process.env.OPENAI_MAX_TOKENS || '1500'),
    });

    if (enableStream) {
      // Handle streaming response
      const encoder = new TextEncoder();
      const readableStream = new ReadableStream({
        async start(controller) {
          try {
            for await (const chunk of response as any) {
              const content = chunk.choices[0]?.delta?.content;
              if (content) {
                const data = JSON.stringify({ content }) + '\n';
                controller.enqueue(encoder.encode(data));
              }
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
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    } else {
      // Handle non-streaming response
      const completion = response as OpenAI.Chat.Completions.ChatCompletion;
      const content = completion.choices[0]?.message?.content || '';
      const data = JSON.stringify({ content }) + '\n';
      
      return new Response(data, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
