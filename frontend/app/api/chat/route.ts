import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { documentSearchTool, executeDocumentSearch } from '../functions/document_search';

// Use Edge Runtime for better streaming performance
export const runtime = 'edge';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Shared constants
const MODEL = process.env.OPENAI_MODEL || 'gpt-5-nano';
const TEMPERATURE = parseFloat(process.env.OPENAI_TEMPERATURE || '1');

// Helper: build image content array (header + images), converting localhost URLs to data URLs in parallel
async function buildImageContent(results: Array<{ image_url: string; label?: string | null; score?: number | null }>, query: string): Promise<any[]> {
  // Build header with labels so model knows what to cite
  const labelsText = results.map((r, i) => `Image ${i + 1}: ${r.label || 'Unknown'}`).join('\n');
  const header = { type: 'input_text', text: `Based on the search results for "${query}", here are the relevant document images:\n\n${labelsText}\n\nWhen citing these images, use the EXACT labels provided above.` } as const;
  
  const items = await Promise.all((results || []).map(async (result, index) => {
    try {
      let imageUrl = result.image_url;
      const isLocal = imageUrl.includes('localhost') || imageUrl.includes('127.0.0.1');
      if (process.env.PUBLIC_MINIO_URL_SET === 'true') {
        imageUrl = imageUrl.replace('localhost', 'minio') || imageUrl.replace('127.0.0.1', 'minio');
      }
      if (isLocal) {
        // Add timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout per image
        
        const imageResponse = await fetch(imageUrl, { signal: controller.signal });
        clearTimeout(timeoutId);
        
        if (!imageResponse.ok) {
          return null;
        }
        
        const imageBuffer = await imageResponse.arrayBuffer();
        const base64 = Buffer.from(imageBuffer).toString('base64');
        const mimeType = imageResponse.headers.get('content-type') || 'image/png';
        const dataUrl = `data:${mimeType};base64,${base64}`;
        
        return { type: 'input_image', image_url: dataUrl } as const;
      }      
      return { type: 'input_image', image_url: imageUrl } as const;
    } catch (error) {
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
  const stream = await openai.responses.create({
    model: MODEL,
    ...(withTools ? { tools: [documentSearchTool] } : {}),
    input: input as any,
    instructions,
    temperature: TEMPERATURE,
    parallel_tool_calls: false,
    stream: true,
  });
  return stream;
}

export async function POST(request: NextRequest) {
  try {
    const { message, k, toolCallingEnabled } = await request.json();

    const systemPrompt = `
    You are a helpful PDF assistant. Use only the provided page images to answer the user's question. 
    If the answer isn't contained in the pages, say you cannot find it.

    FORMATTING GUIDELINES:
    - Use **bold** for emphasis and key terms
    - Use *italic* for subtle emphasis
    - Use \`code\` for technical terms or specific values
    - Use bullet points with - for lists
    - Use ## for section headers when organizing longer responses
    - Structure your response with clear paragraphs

    CITATION REQUIREMENTS:
    - ALWAYS cite sources using the EXACT page labels provided in the image results
    - Format citations as: (filename.pdf — Page X of Y) or [filename.pdf — Page X of Y]
    - Place citations immediately after the relevant information
    - Use the complete label exactly as provided - this enables inline image thumbnails
    - Multiple citations: (doc1.pdf — Page 2 of 5, doc2.pdf — Page 3 of 8)
    - Example: "Calcium is essential for bone health (nutrition.pdf — Page 51 of 100)"
    - Do NOT infer page numbers - copy the exact label from the search results
    - The exact label format ensures users see clickable image previews inline

    You will have access to the following tools:
    ${documentSearchTool.description}

    If the user asks you to search for relevant documents and images based on a query, use the document_search tool. 
    The tool will return a list of image URLs with labels that you must use for citations.
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
        model: MODEL,
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
    let kbItems: Array<{ image_url?: string | null; label?: string | null; score?: number | null }> | null = null;
    // When tool calling is disabled, always run knowledgebase search
    if (!toolEnabled) {
      const searchResult = await executeDocumentSearch(message, kClamped);
      
      if (searchResult.success && searchResult.results && searchResult.results.length > 0) {
        // Build image content - this is the bottleneck!
        const imageContent = await buildImageContent(searchResult.results, message);
        appendUserImages(input, imageContent);
        // capture rich results to emit to client
        kbItems = Array.isArray(searchResult.results) ? searchResult.results : null;
      }
      // Now, generate answer WITHOUT tools
      streamResponse = await streamModel({ input, instructions: systemPrompt, withTools: false });
    } else {
      if (functionCall && functionCall.name === 'document_search') {
        const searchResult = await executeDocumentSearch(message, kClamped);

        // 4. Add function result to input
        input.push({
          type: "function_call_output",
          call_id: functionCall.call_id,
          output: JSON.stringify(searchResult),
        } as any);

        // 5. Add retrieved images as visual input for the model to analyze
        if (searchResult.success && searchResult.results && searchResult.results.length > 0) {
          // Build image content - this is the bottleneck!
          const imageContent = await buildImageContent(searchResult.results, message);
          appendUserImages(input, imageContent);
          // capture rich results to emit to client
          kbItems = Array.isArray(searchResult.results) ? searchResult.results : null;
        }
      }

      // Continue streaming WITH tools enabled
      streamResponse = await streamModel({ input, instructions: systemPrompt, withTools: true });
    }


    const encoder = new TextEncoder();
    
    // Create a TransformStream to ensure immediate flushing
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    
    // Start streaming in the background
    (async () => {
      try {
        // Send initial comment to force stream to open immediately
        await writer.write(encoder.encode(`: stream-start\n\n`));
        
        // Send KB images FIRST to show citations immediately
        if (kbItems && kbItems.length > 0) {
          const kbPayload = JSON.stringify({ event: 'kb.images', data: { items: kbItems } });
          await writer.write(encoder.encode(`data: ${kbPayload}\n\n`));
        }
        
        // Now stream the model response
        for await (const event of streamResponse as any) {
          // Send all events as SSE lines
          const payload = JSON.stringify({ event: event.type, data: event });
          await writer.write(encoder.encode(`data: ${payload}\n\n`));
        }
        await writer.close();
      } catch (error) {
        console.error('Stream error:', error);
        await writer.abort(error);
      }
    })();

    return new Response(readable, {
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
