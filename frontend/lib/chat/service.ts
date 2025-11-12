import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import type { Stream } from "openai/streaming";
import { RetrievalService } from "@/lib/api/generated";
import { appendCitationReminder, appendUserImages, buildImageContent, buildMarkdownContent } from "@/lib/chat/content";
import { createInitialToolResponse, createStreamingResponse } from "@/lib/chat/openai";
import { buildSystemInstructions } from "@/lib/chat/prompt";
import type { NormalizedChatRequest } from "@/lib/chat/types";
import { loadConfigFromStorage } from "@/lib/config/config-store";
import { logger } from "@/lib/utils/logger";

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
        try {
            const results = await RetrievalService.searchSearchGet(
                options.message,
                options.k,
                ocrEnabled
            );
            if (results && results.length > 0) {
                await attachSearchResults(results);
            }
        } catch (error) {
            logger.error('Search failed', { error, query: options.message });
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
        let searchResult: any;

        try {
            const results = await RetrievalService.searchSearchGet(
                options.message,
                options.k,
                ocrEnabled
            );
            const imageUrls = results
                .map((result) => result.image_url)
                .filter((url): url is string => typeof url === "string" && url.length > 0);

            searchResult = {
                success: true,
                query: options.message,
                images: imageUrls,
                results: results,
                count: imageUrls.length
            };

            if (results && results.length > 0) {
                await attachSearchResults(results);
            }
        } catch (error) {
            console.error('Search failed:', error);
            searchResult = {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
                query: options.message
            };
        }

        input.push({
            type: "function_call_output",
            call_id: functionCall.call_id,
            output: JSON.stringify(searchResult),
        } as any);
    }

    const stream = await createStreamingResponse({
        input,
        instructions,
        reasoningEffort: options.reasoningEffort,
        withTools: !toolUsed,
    });

    return { stream, kbItems };
}
