import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { documentSearchTool, executeDocumentSearch } from '../functions/document_search';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Shared constants
const MODEL = process.env.OPENAI_MODEL || 'gpt-5-nano';
const TEMPERATURE = parseFloat(process.env.OPENAI_TEMPERATURE || '1');

type KnowledgeBaseItem = {
  image_url?: string | null;
  label?: string | null;
  score?: number | null;
};

const systemPrompt = `
You are a helpful PDF assistant. Use only the provided page images to answer the user's question.
If the answer is not contained in the pages, clearly say you cannot find it.

FORMATTING GUIDELINES:
- Use **bold** for emphasis and key terms
- Use *italic* for subtle emphasis
- Use \`code\` for technical terms or specific values
- Use - for bullet lists
- Use ## for section headers when organizing longer responses
- Structure your response with clear paragraphs

CITATION REQUIREMENTS:
- ALWAYS cite sources using the exact page labels provided in the search results (example: report.pdf - Page 2 of 10)
- Place citations immediately after the relevant information using parentheses or brackets
- Copy the labels exactly as written so the UI can attach the preview (do not rewrite or abbreviate them)
- If a statement cannot be supported by the labels, omit it or explain that no supporting evidence was found
- Never fabricate labels, page numbers, or citations. If you lack supporting evidence, state that explicitly.

You have access to the following tool:
${documentSearchTool.description}

When the user asks for information from the documents, call the document_search tool and base your answer only on the returned images and labels.
`.trim();

// Helper: build image content array (header + images), converting localhost URLs to data URLs in parallel
async function buildImageContent(results: KnowledgeBaseItem[], query: string): Promise<any[]> {
  // Build header with labels so model knows what to cite
  const labelsText = (results || [])
    .map((r, i) => `Image ${i + 1}: ${r.label || 'Unknown'}`)
    .join('\n');
  const header = {
    type: 'input_text',
    text: `Based on the search results for "${query}", here are the relevant document images:\n\n${labelsText}\n\nWhen citing these images, use the EXACT labels provided above.`,
  } as const;

  const items = await Promise.all((results || []).map(async (result) => {
    try {
      let imageUrl = result.image_url;
      if (!imageUrl) {
        return null;
      }

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

function appendCitationReminder(input: any[], results: KnowledgeBaseItem[] | null) {
  if (!results || results.length === 0) {
    return;
  }

  const labelLines = results
    .map((result, index) => (result.label ? `${index + 1}. ${result.label}` : null))
    .filter(Boolean)
    .join('\n');

  const reminderSections = [
    'Use only the retrieved document images to answer.',
    'Every factual statement must include an inline citation using one of the exact labels provided.',
    'If a statement cannot be supported by these labels, omit it or explain that no supporting evidence was found.',
  ];

  if (labelLines) {
    reminderSections.push('Available citation labels:\n' + labelLines);
  }

  input.push({
    role: 'system',
    content: [{ type: 'input_text', text: reminderSections.join('\n') }],
  } as any);
}

// Helper: stream a model response with or without tools
async function streamModel(params: { input: any[]; instructions: string; withTools: boolean }) {
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

    const userMessage = typeof message === 'string' ? message.trim() : '';

    // Basic validation & defaults (backend guards)
    if (!userMessage) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }
    const kNum = Number.isFinite(Number(k)) ? Number(k) : 5;
    // bound k to reasonable limits (mirror UI: 1..25)
    const kClamped = Math.max(1, Math.min(25, kNum));

    // Create running input list following OpenAI guide pattern
    let input: any[] = [
      { role: 'system', content: [{ type: 'input_text', text: systemPrompt }] },
      { role: 'user', content: [{ type: 'input_text', text: userMessage }] },
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
        temperature: TEMPERATURE,
        parallel_tool_calls: false,
      });
    }

    // 2. Check for function calls and execute them
    let functionCall: any = null;
    let functionCallArguments: any = null;
    if (toolEnabled && response?.output) {
      input = input.concat(response.output as any);
      response.output.forEach((item: any) => {
        if (item.type === 'function_call') {
          functionCall = item;
          functionCallArguments = JSON.parse(item.arguments);
        }
      });
    }

    // 3. Execute function if called
    let streamResponse: any;
    let kbItems: KnowledgeBaseItem[] | null = null;
    // When tool calling is disabled, always run knowledgebase search
    if (!toolEnabled) {
      const searchResult = await executeDocumentSearch(userMessage, kClamped);

      if (searchResult.success && searchResult.results && searchResult.results.length > 0) {
        // Build image content - this is the bottleneck!
        const imageContent = await buildImageContent(searchResult.results, userMessage);
        appendUserImages(input, imageContent);
        // capture rich results to emit to client
        kbItems = Array.isArray(searchResult.results) ? searchResult.results : null;
        appendCitationReminder(input, kbItems);
      }
      // Now, generate answer WITHOUT tools
      streamResponse = await streamModel({ input, instructions: systemPrompt, withTools: false });
    } else {
      let toolUsed = false;
      if (functionCall && functionCall.name === 'document_search') {
        toolUsed = true;
        const searchResult = await executeDocumentSearch(userMessage, kClamped);

        // 4. Add function result to input
        input.push({
          type: 'function_call_output',
          call_id: functionCall.call_id,
          output: JSON.stringify(searchResult),
        } as any);

        // 5. Add retrieved images as visual input for the model to analyze
        if (searchResult.success && searchResult.results && searchResult.results.length > 0) {
          // Build image content - this is the bottleneck!
          const imageContent = await buildImageContent(searchResult.results, userMessage);
          appendUserImages(input, imageContent);
          // capture rich results to emit to client
          kbItems = Array.isArray(searchResult.results) ? searchResult.results : null;
          appendCitationReminder(input, kbItems);
        }
      }

      // Continue streaming WITH tools enabled
      streamResponse = await streamModel({
        input,
        instructions: systemPrompt,
        withTools: !toolUsed,
      });
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
      { status: 500 },
    );
  }
}
