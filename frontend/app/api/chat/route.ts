import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { documentSearchTool, executeDocumentSearch } from '../functions/document_search';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Shared constants
const MODEL = process.env.OPENAI_MODEL || 'gpt-5-nano';
const TEMPERATURE = parseFloat(process.env.OPENAI_TEMPERATURE || '1');

// Helper: build image content array (header + images), converting localhost URLs to data URLs in parallel
async function buildImageContent(images: string[], query: string): Promise<any[]> {
  const header = { type: 'input_text', text: `Based on the search results for "${query}", here are the relevant document images:` } as const;
  const items = await Promise.all((images || []).map(async (imageUrl) => {
    try {
      const isLocal = imageUrl.includes('localhost') || imageUrl.includes('127.0.0.1');
      if (isLocal) {
        const imageResponse = await fetch(imageUrl);
        if (!imageResponse.ok) return null;
        const imageBuffer = await imageResponse.arrayBuffer();
        const base64 = Buffer.from(imageBuffer).toString('base64');
        const mimeType = imageResponse.headers.get('content-type') || 'image/png';
        const dataUrl = `data:${mimeType};base64,${base64}`;
        return { type: 'input_image', image_url: dataUrl } as const;
      }
      return { type: 'input_image', image_url: imageUrl } as const;
    } catch (error) {
      console.warn(`Error processing image: ${imageUrl}`, error);
      return null;
    }
  }));
  return [header, ...items.filter(Boolean)];
}

// Helper: append a user message containing image content
function appendUserImages(input: any[], imageContent: any[]) {
  input.push({
    role: 'user',
    content: imageContent,
  } as any);
}

// Helper: stream a model response with or without tools
async function streamModel(params: { input: any[]; instructions: string; withTools: boolean; }) {
  const { input, instructions, withTools } = params;
  return openai.responses.create({
    model: MODEL,
    ...(withTools ? { tools: [documentSearchTool] } : {}),
    input: input as any,
    instructions,
    temperature: TEMPERATURE,
    parallel_tool_calls: false,
    stream: true,
  });
}

export async function POST(request: NextRequest) {
  try {
    const { message, k, toolCallingEnabled } = await request.json();

    const systemPrompt = `
    You are a helpful PDF assistant. Use only the provided page images to answer the user's question. 
    If the answer isn't contained in the pages, say you cannot find it. Be concise and always mention from which pages the answer is taken.

    You will have access to the following tools:
    ${documentSearchTool.description}

    If the user asks you to search for relevant documents and images based on a query, use the document_search tool. 
    The tool will return a list of image URLs that you can use to answer the user's question.
    
    Cite pages using the labels above (do not infer by result order).
    `

    // Basic validation & defaults (backend guards)
    if (typeof message !== 'string' || !message.trim()) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }
    const kNum = Number.isFinite(Number(k)) ? Number(k) : 5;
    // bound k to reasonable limits (mirror UI: 1..25)
    const kClamped = Math.max(1, Math.min(25, kNum));

    // Create running input list following OpenAI guide pattern
    let input: any[] = [
      { role: 'user', content: message }
    ];

    const toolEnabled = toolCallingEnabled !== false; // default to true

    let response: any | undefined;
    if (toolEnabled) {
      // 1. Initial API call with tools defined
      response = await openai.responses.create({
        model: process.env.OPENAI_MODEL || 'gpt-5-nano',
        tools: [documentSearchTool],
        input: input as any,
        instructions: systemPrompt,
        temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
        parallel_tool_calls: false,
      });
    }

    // 2. Check for function calls and execute them
    let functionCall: any = null;
    let functionCallArguments: any = null;
    if (toolEnabled && response?.output) {
      input = input.concat(response.output as any);
      response.output.forEach((item: any) => {
        if (item.type === "function_call") {
          functionCall = item;
          functionCallArguments = JSON.parse(item.arguments);
        }
      });
    }

    // 3. Execute function if called
    let streamResponse: any;
    // When tool calling is disabled, always run knowledgebase search
    if (!toolEnabled) {
      const searchResult = await executeDocumentSearch(message, kClamped);
      if (searchResult.success && searchResult.images && searchResult.images.length > 0) {
        const imageContent = await buildImageContent(searchResult.images, message);
        appendUserImages(input, imageContent);
      }
      // Now, generate answer WITHOUT tools
      streamResponse = await streamModel({ input, instructions: systemPrompt, withTools: false });
    } else {
      if (functionCall && functionCall.name === 'document_search') {
        const searchResult = await executeDocumentSearch(functionCallArguments.query, kClamped);

        // 4. Add function result to input
        input.push({
          type: "function_call_output",
          call_id: functionCall.call_id,
          output: JSON.stringify(searchResult),
        } as any);

        // 5. Add retrieved images as visual input for the model to analyze
        if (searchResult.success && searchResult.images && searchResult.images.length > 0) {
          const imageContent = await buildImageContent(searchResult.images, functionCallArguments.query);
          appendUserImages(input, imageContent);
        }
      }

      // Continue streaming WITH tools enabled
      streamResponse = await streamModel({ input, instructions: systemPrompt, withTools: true });
    }


    const encoder = new TextEncoder();
    const readableStream = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          for await (const event of streamResponse as any) {
            // Send all events as SSE lines
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
