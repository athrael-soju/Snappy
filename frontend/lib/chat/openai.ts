import OpenAI from "openai";
import type { Stream } from "openai/streaming";
import { documentSearchTool } from "@/lib/api/functions/document_search";
import type { ReasoningEffort } from "@/lib/chat/types";
import type { Message, StreamEvent } from "@/lib/chat/openai-types";

export const MODEL = process.env.OPENAI_MODEL || "gpt-5-nano";
export const TEMPERATURE = parseFloat(process.env.OPENAI_TEMPERATURE || "1");

let openaiClient: OpenAI | null = null;

export function getOpenAIClient(): OpenAI {
    if (!openaiClient) {
        const apiKey = process.env.OPENAI_API_KEY;
        if (!apiKey) {
            throw new Error("OPENAI_API_KEY environment variable is not set. Please check your .env.local file.");
        }
        openaiClient = new OpenAI({ apiKey });
    }
    return openaiClient;
}

type CreateResponseBaseParams = {
    input: Message[];
    instructions: string;
    reasoningEffort: ReasoningEffort;
};

export async function createInitialToolResponse(params: CreateResponseBaseParams) {
    const { input, instructions, reasoningEffort } = params;
    const client = getOpenAIClient();
    return client.responses.create({
        model: MODEL,
        tools: [documentSearchTool],
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        input: input as any, // OpenAI SDK accepts complex message format
        instructions,
        temperature: TEMPERATURE,
        parallel_tool_calls: false,
        reasoning: { effort: reasoningEffort },
    });
}

export async function createStreamingResponse(params: CreateResponseBaseParams & { withTools: boolean }): Promise<Stream<StreamEvent>> {
    const { input, instructions, reasoningEffort, withTools } = params;
    const client = getOpenAIClient();
    const payload: Record<string, unknown> = {
        model: MODEL,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        input: input as any, // OpenAI SDK accepts complex message format
        instructions,
        temperature: TEMPERATURE,
        parallel_tool_calls: false,
        stream: true,
        reasoning: { effort: reasoningEffort },
    };

    if (withTools) {
        payload.tools = [documentSearchTool];
    }

    return client.responses.create(payload) as unknown as Promise<Stream<StreamEvent>>;
}
