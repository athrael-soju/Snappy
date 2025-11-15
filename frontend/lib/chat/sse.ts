import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import type { StreamEvent } from "./openai-types";
import { logger } from "@/lib/utils/logger";

type CreateSSEStreamParams = {
    stream: AsyncIterable<StreamEvent>;
    kbItems: SearchItem[] | null;
    onError?: (error: unknown) => void;
};

export function createSSEStream({ stream, kbItems, onError }: CreateSSEStreamParams): Response {
    const encoder = new TextEncoder();
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();

    (async () => {
        try {
            await writer.write(encoder.encode(`: stream-start\n\n`));

            if (kbItems && kbItems.length > 0) {
                const kbPayload = JSON.stringify({ event: "kb.images", data: { items: kbItems } });
                await writer.write(encoder.encode(`data: ${kbPayload}\n\n`));
            }

            for await (const event of stream) {
                const payload = JSON.stringify({ event: event.type, data: event });
                await writer.write(encoder.encode(`data: ${payload}\n\n`));
            }

            // Append citations after stream completes
            if (kbItems && kbItems.length > 0) {
                const citations = kbItems
                    .map((item, index) => `${index + 1}. [${item.label || 'Unknown'}](${item.image_url || '#'})`)
                    .join('\n');
                const citationText = `\n\n---\n\n**Sources:**\n\n${citations}`;

                // Send citation as text delta to append to same message bubble
                const citationEvent = {
                    event: 'response.output_text.delta',
                    data: {
                        delta: citationText
                    }
                };

                const citationPayload = JSON.stringify(citationEvent);
                await writer.write(encoder.encode(`data: ${citationPayload}\n\n`));
            }

            await writer.close();
        } catch (error) {
            logger.error('SSE stream error', { error });
            onError?.(error);
            await writer.abort(error);
        }
    })();

    return new Response(readable, {
        headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
            "X-Accel-Buffering": "no",
        },
    });
}
