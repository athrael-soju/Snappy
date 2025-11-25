import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import type { Stream } from "openai/streaming";
import "@/lib/api/client"; // Initialize OpenAPI base URL
import { RetrievalService } from "@/lib/api/generated";
import { buildImageContent, buildMarkdownContent, buildRegionImagesContent } from "@/lib/chat/content";
import { createInitialToolResponse, createStreamingResponse } from "@/lib/chat/openai";
import { buildSystemInstructions } from "@/lib/chat/prompt";
import type { NormalizedChatRequest } from "@/lib/chat/types";
import type { Message, StreamEvent, FunctionCallOutput, SearchToolResult } from "@/lib/chat/openai-types";
import { logger } from "@/lib/utils/logger";

export type ChatServiceResult = {
    stream: Stream<StreamEvent>;
    kbItems: SearchItem[] | null;
};

export async function runChatService(options: NormalizedChatRequest): Promise<ChatServiceResult> {
    // Use config flags passed from client (server doesn't have localStorage access)
    const ocrEnabled = options.ocrEnabled;
    const ocrIncludeImages = options.ocrIncludeImages;
    const interpretabilityEnabled = options.interpretabilityEnabled;
    const instructions = buildSystemInstructions(options.summaryPreference, ocrEnabled, ocrIncludeImages);

    let input: Message[] = [
        { role: "system", content: [{ type: "input_text", text: instructions }] },
        { role: "user", content: [{ type: "input_text", text: options.message }] },
    ];

    let kbItems: SearchItem[] | null = null;

    const attachSearchResults = async (results: SearchItem[] | null) => {
        if (!results || results.length === 0) {
            return;
        }

        // Use OCR-based (markdown) content if OCR is enabled AND OCR data exists
        // Check inline payload (markdown or regions) and json_url for backward compatibility
        const hasOcrData = results.some((result) =>
            result?.payload?.ocr?.markdown ||
            result?.payload?.ocr?.regions?.length > 0 ||
            result?.json_url
        );
        const useOcrContent = ocrEnabled && hasOcrData;

        let searchContent: any[];

        if (useOcrContent && ocrIncludeImages) {
            // When both OCR and region images are enabled:
            // - Send OCR text + region images (cropped figures/tables) to LLM
            // - Full page images are available in kbItems for citations
            const markdownContent = await buildMarkdownContent(results, options.message);
            const regionImages = await buildRegionImagesContent(results, options.message);

            // Combine: OCR text + region image items (skip region header at index 0)
            searchContent = [...markdownContent, ...regionImages.slice(1)];
        } else if (useOcrContent) {
            // Only OCR text (when ocrIncludeImages is false or not set)
            searchContent = await buildMarkdownContent(results, options.message);
        } else {
            // Only full page images (when OCR is disabled or no OCR data exists)
            searchContent = await buildImageContent(results, options.message);
        }

        // Combine user query text with search results into a single user message
        // Remove the initial user message and replace with combined content
        input = [
            input[0], // Keep system message
            {
                role: "user",
                content: [
                    { type: "input_text", text: options.message },
                    ...searchContent
                ]
            }
        ];

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
        input = input.concat(initialOutputs as unknown as Message[]);
    }

    let toolUsed = false;
    const functionCall = initialOutputs.find((item): item is FunctionCallOutput => item?.type === "function_call") as FunctionCallOutput | undefined;

    if (functionCall && functionCall.name === "document_search") {
        toolUsed = true;
        let searchResult: SearchToolResult;

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
            role: "user",
            content: [{
                type: "function_call_output",
                call_id: functionCall.call_id,
                output: JSON.stringify(searchResult),
            }],
        });
    }

    const stream = await createStreamingResponse({
        input,
        instructions,
        reasoningEffort: options.reasoningEffort,
        withTools: !toolUsed,
    });

    return { stream, kbItems };
}
