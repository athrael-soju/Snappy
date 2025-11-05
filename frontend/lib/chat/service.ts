import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import type { Stream } from "openai/streaming";
import { executeDocumentSearch } from "@/lib/api/functions/document_search";
import { appendCitationReminder, appendUserImages, buildImageContent, buildMarkdownContent } from "@/lib/chat/content";
import { createInitialToolResponse, createStreamingResponse } from "@/lib/chat/openai";
import { buildSystemInstructions } from "@/lib/chat/prompt";
import type { NormalizedChatRequest } from "@/lib/chat/types";

export type ChatServiceResult = {
    stream: Stream<any>;
    kbItems: SearchItem[] | null;
};

export async function runChatService(options: NormalizedChatRequest): Promise<ChatServiceResult> {
    const instructions = buildSystemInstructions(options.summaryPreference);

    let input: any[] = [
        { role: "system", content: [{ type: "input_text", text: instructions }] },
        { role: "user", content: [{ type: "input_text", text: options.message }] },
    ];

    let kbItems: SearchItem[] | null = null;

    const attachSearchResults = async (results: SearchItem[] | null) => {
        if (!results || results.length === 0) {
            return;
        }

        const hasOcrData = results.some((result: any) => result?.json_url);
        const content = hasOcrData
            ? await buildMarkdownContent(results, options.message)
            : await buildImageContent(results, options.message);

        appendUserImages(input, content);
        appendCitationReminder(input, results);
        kbItems = results;
    };

    if (!options.toolCallingEnabled) {
        const searchResult = await executeDocumentSearch(options.message, options.k);
        if (searchResult.success && Array.isArray(searchResult.results) && searchResult.results.length > 0) {
            await attachSearchResults(searchResult.results as SearchItem[]);
        }

        const stream = await createStreamingResponse({
            input,
            instructions,
            reasoningEffort: options.reasoningEffort,
            withTools: false,
        });

        return { stream, kbItems };
    }

    const initialResponse = await createInitialToolResponse({
        input,
        instructions,
        reasoningEffort: options.reasoningEffort,
    });

    const initialOutputs = Array.isArray(initialResponse?.output) ? initialResponse.output : [];
    if (initialOutputs.length > 0) {
        input = input.concat(initialOutputs as any[]);
    }

    let toolUsed = false;
    const functionCall = initialOutputs.find((item: any) => item?.type === "function_call") as any;

    if (functionCall && functionCall.name === "document_search") {
        toolUsed = true;
        const searchResult = await executeDocumentSearch(options.message, options.k);

        input.push({
            type: "function_call_output",
            call_id: functionCall.call_id,
            output: JSON.stringify(searchResult),
        } as any);

        if (searchResult.success && Array.isArray(searchResult.results) && searchResult.results.length > 0) {
            await attachSearchResults(searchResult.results as SearchItem[]);
        }
    }

    const stream = await createStreamingResponse({
        input,
        instructions,
        reasoningEffort: options.reasoningEffort,
        withTools: !toolUsed,
    });

    return { stream, kbItems };
}
