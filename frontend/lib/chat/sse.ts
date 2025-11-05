import type { SearchItem } from "@/lib/api/generated/models/SearchItem";

type CreateSSEStreamParams = {
    stream: AsyncIterable<any>;
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

            for await (const event of stream as any) {
                const payload = JSON.stringify({ event: event.type, data: event });
                await writer.write(encoder.encode(`data: ${payload}\n\n`));
            }

            await writer.close();
        } catch (error) {
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
