import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { baseUrl } from '@/lib/api/client';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { message, systemPrompt, model } = await request.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Helper to convert possibly-private image URLs to inline data URLs
    async function toImagePart(url: string) {
      const isHttp = url.startsWith('http://') || url.startsWith('https://');
      const isLocal = /(^http:\/\/localhost)|(^http:\/\/127\.0\.0\.1)|(^https:\/\/localhost)|(^https:\/\/127\.0\.0\.1)/.test(
        url
      );
      if (isHttp && !isLocal) return { type: 'input_image', image_url: url };
      try {
        const imageResponse = await fetch(url);
        if (!imageResponse.ok) {
          console.warn(`Failed to fetch image: ${url} - ${imageResponse.status}`);
          return null;
        }
        const imageBuffer = await imageResponse.arrayBuffer();
        const base64 = Buffer.from(imageBuffer).toString('base64');
        const mimeType = imageResponse.headers.get('content-type') || 'image/jpeg';
        const dataUrl = `data:${mimeType};base64,${base64}`;
        return { type: 'input_image', image_url: dataUrl };
      } catch (error) {
        console.warn(`Error fetching image: ${url}`, error);
        return null;
      }
    }

    // --- Tools (top-level format you provided) ---
    const tools = [
      {
        type: 'function',
        name: 'search_documents',
        description:
          "Search the user's uploaded documents and return the most relevant page images with labels and scores.",
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string', description: "User's question to search for" },
            k: {
              type: 'integer',
              description: 'Number of results to retrieve (1-25)',
              minimum: 1,
              maximum: 25,
              default: 5,
            },
          },
          required: ['query', 'k'],
          additionalProperties: false,
        },
      },
    ] as any;

    // --- Prompts ---
    const kbPrompt =
      "You are a helpful PDF/document assistant. Use only the provided page images to answer the user's question. If the answer isn't contained in the pages, say you cannot find it. Be concise and always mention from which pages the answer is taken.";
    const basePrompt = systemPrompt || 'You are a helpful assistant. Be concise and accurate.';

    // 1) PLANNING: ask the model if it wants to call `search_documents`
    // Using the Responses API tool-calling flow with top-level tool format
    let planningInput: any[] = [
      { role: 'user', content: [{ type: 'input_text', text: message }] },
    ];

    const planning = await openai.responses.create({
      model: model || 'gpt-5-nano',
      tools,
      tool_choice: 'auto',
      parallel_tool_calls: false,
      instructions:
        "Decide whether the user's question requires searching their knowledge base. If the question references any document content (e.g., mentions a case ID/name, pages, PDF sections, summaries, citations), you MUST call search_documents with the query and choose an appropriate k (1-25). Only skip the tool for general chit-chat.",
      input: planningInput,
    });

    // Keep a running input list like in the official pattern
    let inputHistory: any[] = planningInput.concat(planning.output);

    // Extract the first function call (top-level items of type 'function_call')
    let fnCall:
      | { type: 'function_call'; name: string; arguments: string; call_id: string }
      | null = null;

    for (const item of planning.output as any[]) {
      if (item?.type === 'function_call' && item?.name) {
        fnCall = item as any;
        break;
      }
    }

    // Prepare variables for KB
    let retrieved:
      | Array<{ image_url?: string | null; label?: string | null; score?: number | null }>
      | null = null;
    let kbImageParts: any[] = [];
    let finalInstructions = basePrompt;

    // 2) If a tool call was made, execute it, append a function_call_output, and attach images
    if (fnCall && fnCall.name === 'search_documents') {
      let args: { query?: string; k?: number } = {};
      try {
        args = JSON.parse(fnCall.arguments || '{}');
      } catch {
        args = {};
      }
      const query = args.query || message;
      const k = Math.max(1, Math.min(25, Number.isFinite(args.k as number) ? (args.k as number) : 5));

      // Execute your backend search
      try {
        const url = `${baseUrl}/search?q=${encodeURIComponent(query)}&k=${k}`;
        const r = await fetch(url);
        if (r.ok) {
          retrieved = await r.json();
        } else {
          console.warn('KB search HTTP error:', r.status, await r.text().catch(() => ''));
        }
      } catch (err) {
        console.warn('KB search failed', err);
      }

      // Append function_call_output so the model can "see" the tool result structurally
      inputHistory.push({
        type: 'function_call_output',
        call_id: fnCall.call_id,
        output: JSON.stringify({ images: retrieved ?? [] }),
      });

      // Also attach the actual page images so the model can visually parse them
      if (Array.isArray(retrieved) && retrieved.length > 0) {
        const parts: any[] = [];
        for (const item of retrieved) {
          const u = (item.image_url || '').toString();
          if (!u) continue;
          const part = await toImagePart(u);
          if (part) parts.push(part);
        }
        kbImageParts = parts;

        // Strengthen instructions with page labels for clear citations
        finalInstructions = `${kbPrompt}\n\n[Retrieved pages]\n${retrieved
          .map((img, idx) => `Page ${idx + 1}: ${img.label || 'Unlabeled'}`)
          .join('\n')}\n\nCite pages using the labels above (do not infer by result order).`;
      } else {
        // No pages returned
        finalInstructions = kbPrompt;
      }
    }

    // Build the final input for the streamed answer:
    // - prior planning input + function_call (and function_call_output when present)
    // - a user message that carries the KB images (if any) and any user-supplied images
    const finalInput: any[] = [...inputHistory];

    const visualParts: any[] = [];
    if (kbImageParts.length > 0) {
      visualParts.push({ type: 'input_text', text: 'Here are the retrieved pages.' }, ...kbImageParts);
    }
    if (visualParts.length > 0) {
      finalInput.push({ role: 'user', content: visualParts });
    }

    // 3) Stream the final model response via SSE, emitting a side-channel event for KB previews
    const encoder = new TextEncoder();

    const readableStream = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          // Side-channel event for your client to render the KB images/citations UI
          if (retrieved && retrieved.length > 0) {
            const kbEvent = JSON.stringify({ event: 'kb.images', data: { images: retrieved } });
            controller.enqueue(encoder.encode(`data: ${kbEvent}\n\n`));
          }

          // Start streaming the final response
          const events = await openai.responses.create({
            model: model || 'gpt-5-nano',
            tools,
            input: finalInput,
            instructions: finalInstructions,
            temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
            parallel_tool_calls: false,
            stream: true,
          });

          for await (const event of events as any) {
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
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
