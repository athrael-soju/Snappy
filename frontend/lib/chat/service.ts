import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import type { Stream } from "openai/streaming";
import { executeDocumentSearch } from "@/lib/api/functions/document_search";
import { appendCitationReminder, appendUserImages, buildImageContent, buildMarkdownContent } from "@/lib/chat/content";
import { createInitialToolResponse, createStreamingResponse } from "@/lib/chat/openai";
import { buildSystemInstructions } from "@/lib/chat/prompt";
import type { NormalizedChatRequest } from "@/lib/chat/types";
import { loadConfigFromStorage } from "@/lib/config/config-store";

export type ChatServiceResult = {
    stream: Stream<any>;
    kbItems: SearchItem[] | null;
};

/**
 * Check if OCR is enabled in the current configuration
 */
function isOcrEnabled(): boolean {
    const config = loadConfigFromStorage();
    return config?.DEEPSEEK_OCR_ENABLED === "True";
}

export async function runChatService(options: NormalizedChatRequest): Promise<ChatServiceResult> {
    const ocrEnabled = isOcrEnabled();
    const instructions = buildSystemInstructions(options.summaryPreference, ocrEnabled);

    let input: any[] = [
        { role: "system", content: [{ type: "input_text", text: instructions }] },
        { role: "user", content: [{ type: "input_text", text: options.message }] },
    ];

    let kbItems: SearchItem[] | null = null;

    const attachSearchResults = async (results: SearchItem[] | null) => {
        if (!results || results.length === 0) {
            return;
        }

        // Use OCR-based (markdown) content if OCR is enabled AND OCR data exists
        // Check both inline payload and json_url for backward compatibility
        const hasOcrData = results.some((result: any) =>
            result?.payload?.ocr?.markdown || result?.json_url
        );
        const useOcrContent = ocrEnabled && hasOcrData;

        const content = useOcrContent
            ? await buildMarkdownContent(results, options.message)
            : await buildImageContent(results, options.message);

        appendUserImages(input, content);
        appendCitationReminder(input, results, useOcrContent);
        kbItems = results;
    };

    if (!options.toolCallingEnabled) {
        const searchResult = await executeDocumentSearch(options.message, options.k, ocrEnabled);
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
        const searchResult = await executeDocumentSearch(options.message, options.k, ocrEnabled);

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
