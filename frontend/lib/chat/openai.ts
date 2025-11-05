import OpenAI from "openai";
import type { Stream } from "openai/streaming";
import { documentSearchTool } from "@/lib/api/functions/document_search";
import type { ReasoningEffort } from "@/lib/chat/types";

export const MODEL = process.env.OPENAI_MODEL || "gpt-5-nano";
export const TEMPERATURE = parseFloat(process.env.OPENAI_TEMPERATURE || "1");

let openaiClient: OpenAI | null = null;

export function getOpenAIClient(): OpenAI {
    if (!openaiClient) {
        openaiClient = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    }
    return openaiClient;
}

type CreateResponseBaseParams = {
    input: any[];
    instructions: string;
    reasoningEffort: ReasoningEffort;
};

export async function createInitialToolResponse(params: CreateResponseBaseParams) {
    const { input, instructions, reasoningEffort } = params;
    const client = getOpenAIClient();
    return client.responses.create({
        model: MODEL,
        tools: [documentSearchTool],
        input: input as any,
        instructions,
        temperature: TEMPERATURE,
        parallel_tool_calls: false,
        reasoning: { effort: reasoningEffort },
    });
}

export async function createStreamingResponse(params: CreateResponseBaseParams & { withTools: boolean }): Promise<Stream<any>> {
    const { input, instructions, reasoningEffort, withTools } = params;
    const client = getOpenAIClient();
    const payload: Record<string, unknown> = {
        model: MODEL,
        input: input as any,
        instructions,
        temperature: TEMPERATURE,
        parallel_tool_calls: false,
        stream: true,
        reasoning: { effort: reasoningEffort },
    };

    if (withTools) {
        payload.tools = [documentSearchTool];
    }

    return client.responses.create(payload) as unknown as Promise<Stream<any>>;
}
