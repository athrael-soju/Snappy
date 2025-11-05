import { NextRequest, NextResponse } from "next/server";
import { createSSEStream } from "@/lib/chat/sse";
import { runChatService } from "@/lib/chat/service";
import { normalizeChatRequest } from "@/lib/chat/types";

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const normalized = normalizeChatRequest(payload);

    if (!normalized.ok) {
      return NextResponse.json({ error: normalized.error }, { status: 400 });
    }

    const { stream, kbItems } = await runChatService(normalized.value);

    return createSSEStream({
      stream,
      kbItems,
      onError: (error) => {
        console.error("Stream error:", error);
      },
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
