import { NextRequest, NextResponse } from "next/server";
import "@/lib/api/client"; // Initialize OpenAPI base URL
import { createSSEStream } from "@/lib/chat/sse";
import { runChatService } from "@/lib/chat/service";
import { normalizeChatRequest } from "@/lib/chat/types";
import { logger } from "@/lib/utils/logger";

const chatLogger = logger.child({ module: 'chat-api' });

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const normalized = normalizeChatRequest(payload);

    if (!normalized.ok) {
      chatLogger.warn('Invalid chat request', { error: normalized.error });
      return NextResponse.json({ error: normalized.error }, { status: 400 });
    }

    chatLogger.info('Chat request started', {
      messageCount: normalized.value.message.length
    });

    const { stream, kbItems } = await runChatService(normalized.value);

    return createSSEStream({
      stream,
      kbItems,
      onError: (error) => {
        chatLogger.error('Stream error', { error });
      },
    });
  } catch (error) {
    chatLogger.error('Chat API error', { error });
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
