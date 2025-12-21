export const ALLOWED_REASONING_EFFORTS = ["minimal", "low", "medium", "high"] as const;
export type ReasoningEffort = (typeof ALLOWED_REASONING_EFFORTS)[number];

export function resolveReasoningEffort(value: unknown): ReasoningEffort {
    if (typeof value === "string" && (ALLOWED_REASONING_EFFORTS as readonly string[]).includes(value)) {
        return value as ReasoningEffort;
    }
    return "minimal";
}

export const ALLOWED_SUMMARY_OPTIONS = ["auto", "concise", "detailed"] as const;
export type SummaryPreference = (typeof ALLOWED_SUMMARY_OPTIONS)[number];

export function resolveSummaryPreference(value: unknown): SummaryPreference | undefined {
    if (typeof value === "string" && (ALLOWED_SUMMARY_OPTIONS as readonly string[]).includes(value)) {
        return value as SummaryPreference;
    }
    return undefined;
}

export interface ChatRouteBody {
    message: unknown;
    k?: unknown;
    toolCallingEnabled?: unknown;
    reasoning?: unknown;
    summary?: unknown;
    ocrEnabled?: unknown;
    ocrIncludeImages?: unknown;
}

export interface NormalizedChatRequest {
    message: string;
    k: number;
    toolCallingEnabled: boolean;
    reasoningEffort: ReasoningEffort;
    summaryPreference?: SummaryPreference;
    ocrEnabled: boolean;
    ocrIncludeImages: boolean;
}

export function normalizeChatRequest(
    body: ChatRouteBody,
): { ok: true; value: NormalizedChatRequest } | { ok: false; error: string } {
    if (!body || typeof body !== "object") {
        return { ok: false, error: "Invalid request payload" };
    }

    const rawMessage = typeof body.message === "string" ? body.message.trim() : "";
    if (!rawMessage) {
        return { ok: false, error: "Message is required" };
    }

    const rawK = Number.isFinite(Number(body.k)) ? Number(body.k) : 5;
    const kClamped = Math.max(1, Math.min(25, rawK));

    const toolEnabled = body.toolCallingEnabled !== false;

    const incomingReasoning =
        body.reasoning && typeof body.reasoning === "object" ? (body.reasoning as Record<string, unknown>) : null;
    const requestedEffort = incomingReasoning && "effort" in incomingReasoning ? incomingReasoning.effort : undefined;
    const reasoningEffort = resolveReasoningEffort(requestedEffort);

    const summaryPreference = resolveSummaryPreference(body.summary);

    // Parse config flags from client
    const ocrEnabled = typeof body.ocrEnabled === 'boolean' ? body.ocrEnabled : false;
    const ocrIncludeImages = typeof body.ocrIncludeImages === 'boolean' ? body.ocrIncludeImages : false;

    return {
        ok: true,
        value: {
            message: rawMessage,
            k: kClamped,
            toolCallingEnabled: toolEnabled,
            reasoningEffort,
            summaryPreference,
            ocrEnabled,
            ocrIncludeImages,
        },
    };
}
