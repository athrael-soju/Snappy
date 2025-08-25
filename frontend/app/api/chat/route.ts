import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { documentSearchTool, executeDocumentSearch } from '../functions/document_search';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { message, k } = await request.json();

    const systemPrompt = `
    You are a helpful PDF assistant. Use only the provided page images to answer the user's question. 
    If the answer isn't contained in the pages, say you cannot find it. Be concise and always mention from which pages the answer is taken.

    You will have access to the following tools:
    ${documentSearchTool.description}

    If the user asks you to search for relevant documents and images based on a query, use the document_search tool. 
    The tool will return a list of image URLs that you can use to answer the user's question.
    
    Cite pages using the labels above (do not infer by result order).
    `

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Create running input list following OpenAI guide pattern
    let input: any[] = [
      { role: 'user', content: message }
    ];

    // 1. Initial API call with tools defined
    let response = await openai.responses.create({
      model: process.env.OPENAI_MODEL || 'gpt-5-nano',
      tools: [documentSearchTool],
      input: input as any,
      instructions: systemPrompt,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
      parallel_tool_calls: false,
    });

    // 2. Check for function calls and execute them
    let functionCall: any = null;
    let functionCallArguments: any = null;
    input = input.concat(response.output as any);

    response.output.forEach((item: any) => {
      if (item.type === "function_call") {
        functionCall = item;
        functionCallArguments = JSON.parse(item.arguments);
      }
    });

    // 3. Execute function if called
    let streamResponse: any;
    if (functionCall && functionCall.name === 'document_search') {
      const searchResult = await executeDocumentSearch(functionCallArguments.query, k);

      // 4. Add function result to input
      input.push({
        type: "function_call_output",
        call_id: functionCall.call_id,
        output: JSON.stringify(searchResult),
      } as any);

      // 5. Add retrieved images as visual input for the model to analyze
      if (searchResult.success && searchResult.images && searchResult.images.length > 0) {
        const imageContent: any[] = [
          { type: 'input_text', text: `Based on the search results for "${functionCallArguments.query}", here are the relevant document images:` }
        ];
        
        // Convert localhost URLs to data URLs for OpenAI
        for (const imageUrl of searchResult.images) {
          try {
            const isLocal = imageUrl.includes('localhost') || imageUrl.includes('127.0.0.1');
            
            if (isLocal) {
              // Fetch the image and convert to data URL
              const imageResponse = await fetch(imageUrl);
              if (imageResponse.ok) {
                const imageBuffer = await imageResponse.arrayBuffer();
                const base64 = Buffer.from(imageBuffer).toString('base64');
                const mimeType = imageResponse.headers.get('content-type') || 'image/png';
                const dataUrl = `data:${mimeType};base64,${base64}`;
                
                imageContent.push({ 
                  type: 'input_image', 
                  image_url: dataUrl 
                });
              } else {
                console.warn(`Failed to fetch image: ${imageUrl} - ${imageResponse.status}`);
              }
            } else {
              // Public URL - use as-is
              imageContent.push({ 
                type: 'input_image', 
                image_url: imageUrl 
              });
            }
          } catch (error) {
            console.warn(`Error processing image: ${imageUrl}`, error);
          }
        }

        // Add user message with images for the model to analyze
        input.push({
          role: 'user',
          content: imageContent
        } as any);
      }

    }

    streamResponse = await openai.responses.create({
      model: process.env.OPENAI_MODEL || 'gpt-5-nano',
      tools: [documentSearchTool],
      input: input as any,
      instructions: systemPrompt,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '1'),
      parallel_tool_calls: false,
      stream: true,
    });


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
