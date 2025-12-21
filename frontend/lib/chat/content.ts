import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import { logger } from '@/lib/utils/logger';

type DataUrl = { mime: string; base64: string };

// Cache for OCR JSON data to avoid duplicate fetches
const ocrDataCache = new Map<string, any>();

async function fetchOcrData(result: SearchItem): Promise<any> {
    // Check if OCR data is inline in payload
    const ocrData = result.payload?.ocr;
    if (ocrData) {
        return ocrData;
    }

    // Storage mode: fetch from json_url
    if (result.json_url) {
        // Check cache first
        if (ocrDataCache.has(result.json_url)) {
            return ocrDataCache.get(result.json_url);
        }

        // Fetch and cache
        const jsonResponse = await fetch(result.json_url);
        if (jsonResponse.ok) {
            const jsonData = await jsonResponse.json();
            ocrDataCache.set(result.json_url, jsonData);
            return jsonData;
        }
    }

    return null;
}

async function fetchImageAsDataUrl(url: string): Promise<DataUrl> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to fetch image: ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const mime = response.headers.get("content-type") || "image/png";
    return { mime, base64: Buffer.from(buffer).toString("base64") };
}

async function inlineLocalImages(markdown: string): Promise<string> {
    if (!markdown || !markdown.includes("![")) {
        return markdown;
    }

    const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
    const matches = Array.from(markdown.matchAll(imageRegex));
    if (matches.length === 0) {
        return markdown;
    }

    type Replacement = { start: number; end: number; value: string };
    const replacements: Replacement[] = [];
    const cache = new Map<string, string>();

    for (const match of matches) {
        const alt = match[1] ?? "";
        const url = match[2]?.trim();
        if (!url) {
            continue;
        }

        const isLocal = url.includes("localhost") || url.includes("127.0.0.1");
        if (!isLocal) {
            continue;
        }

        const cacheKey = `${alt}::${url}`;
        if (!cache.has(cacheKey)) {
            let resolvedUrl = url;
            if (process.env.PUBLIC_STORAGE_URL_SET === "true") {
                resolvedUrl = resolvedUrl
                    .replace("localhost", "backend")
                    .replace("127.0.0.1", "backend");
            }

            const createMarkdownImage = (data: DataUrl) =>
                `![${alt}](data:${data.mime};base64,${data.base64})`;

            try {
                const dataUrl = await fetchImageAsDataUrl(resolvedUrl);
                cache.set(cacheKey, createMarkdownImage(dataUrl));
            } catch (error) {
                if (resolvedUrl !== url) {
                    try {
                        const dataUrl = await fetchImageAsDataUrl(url);
                        cache.set(cacheKey, createMarkdownImage(dataUrl));
                    } catch {
                        continue;
                    }
                } else {
                    continue;
                }
            }
        }

        const replacement = cache.get(cacheKey);
        if (!replacement) {
            continue;
        }

        const start = match.index ?? 0;
        const end = start + match[0].length;
        replacements.push({ start, end, value: replacement });
    }

    if (replacements.length === 0) {
        return markdown;
    }

    replacements.sort((a, b) => b.start - a.start);
    let updated = markdown;
    for (const { start, end, value } of replacements) {
        updated = `${updated.slice(0, start)}${value}${updated.slice(end)}`;
    }

    return updated;
}

export async function buildImageContent(results: SearchItem[], query: string): Promise<any[]> {
    logger.info(`[buildImageContent] Processing ${results?.length ?? 0} results for query: "${query}"`);

    const labelsText = (results || [])
        .map((result, index) => `Image ${index + 1}: ${result.label || "Unknown"}`)
        .join("\n");

    const header = {
        type: "input_text",
        text: `Based on the search results for "${query}", here are the relevant document images:\n\n${labelsText}\n\nWhen citing these images, use the EXACT labels provided above.`,
    } as const;

    const items = await Promise.all(
        (results || []).map(async (result, index) => {
            try {
                let imageUrl = result.image_url;
                if (!imageUrl) {
                    logger.warn(`[buildImageContent] Result ${index} has no image_url`);
                    return null;
                }

                logger.debug(`[buildImageContent] Result ${index} image_url: ${imageUrl}`);

                // Always fetch and convert to base64 - OpenAI can't access local/private URLs
                let fetchUrl = imageUrl;
                if (process.env.PUBLIC_STORAGE_URL_SET === "true") {
                    fetchUrl = fetchUrl.replace("localhost", "backend").replace("127.0.0.1", "backend");
                }

                logger.debug(`[buildImageContent] Fetching image ${index} from: ${fetchUrl}`);
                const imageResponse = await fetch(fetchUrl);
                if (!imageResponse.ok) {
                    logger.error(`[buildImageContent] Failed to fetch image ${index}: ${imageResponse.status} ${imageResponse.statusText}`);
                    return null;
                }

                const imageBuffer = await imageResponse.arrayBuffer();
                const base64 = Buffer.from(imageBuffer).toString("base64");
                const mimeType = imageResponse.headers.get("content-type") || "image/png";
                const dataUrl = `data:${mimeType};base64,${base64}`;

                logger.debug(`[buildImageContent] Result ${index} converted to base64 (${base64.length} chars)`);
                return { type: "input_image", image_url: dataUrl } as const;
            } catch (error) {
                logger.error(`[buildImageContent] Error processing result ${index}`, { error });
                return null;
            }
        }),
    );

    const validItems = items.filter(Boolean);
    logger.info(`[buildImageContent] Returning ${validItems.length} valid image items`);
    return [header, ...validItems];
}

export async function buildMarkdownContent(results: SearchItem[], query: string): Promise<any[]> {
    // Build a unified text block containing all pages
    const pageContents: string[] = [];
    const IMAGE_REGION_LABELS = ['figure', 'diagram', 'image', 'chart', 'graph'];

    // Parallelize OCR data fetches
    const fetchTasks = (results || []).map(async (result) => {
        try {
            const ocrData = await fetchOcrData(result);
            if (!ocrData) return null;

            let pageText: string | null = null;

            // Try pre-formatted fields first
            // Priority: markdown > text > raw_text
            pageText = ocrData.markdown || ocrData.text || ocrData.raw_text || null;

            // If no pre-formatted fields, build from regions
            if (!pageText && ocrData.regions && Array.isArray(ocrData.regions)) {
                // Exclude image regions (their content is URLs, not text)
                const regionTexts = ocrData.regions
                    .filter((region: any) => !IMAGE_REGION_LABELS.includes(region.label?.toLowerCase()))
                    .map((region: any) => region.content || '')
                    .filter((text: string) => text.trim())
                    .join('\n\n');

                if (regionTexts) {
                    pageText = regionTexts;
                }
            }

            // Inline local images in markdown if present
            if (pageText && ocrData.markdown) {
                pageText = await inlineLocalImages(pageText);
            }

            if (pageText && pageText.trim()) {
                return {
                    label: result.label || "Unknown",
                    text: pageText.trim()
                };
            }

            return null;
        } catch (error) {
            logger.error('Failed to process OCR content', { error, label: result.label });
            return null;
        }
    });

    // Wait for all fetches to complete in parallel
    const fetchedPages = await Promise.all(fetchTasks);

    // Build page contents from fetched data
    for (const page of fetchedPages) {
        if (page) {
            pageContents.push(`## ${page.label}\n\n${page.text}`);
        }
    }

    if (pageContents.length === 0) {
        return [];
    }

    // Build label list for reference
    const labelsText = (results || [])
        .map((result, index) => `${index + 1}. ${result.label || "Unknown"}`)
        .join("\n");

    // Combine everything into ONE single text content item
    const unifiedText = `Based on the search results for "${query}", here are the relevant document contents:

**Available Documents:**
${labelsText}

**Important:** When citing information, use the EXACT document labels shown above.

---

${pageContents.join("\n\n---\n\n")}`;

    return [{
        type: "input_text",
        text: unifiedText,
    } as const];
}

export async function buildRegionImagesContent(results: SearchItem[], query: string): Promise<any[]> {
    const IMAGE_REGION_LABELS = ['figure', 'diagram', 'image', 'chart', 'graph'];

    // Helper function to fetch and convert image to base64
    async function fetchRegionImage(imageUrl: string): Promise<any | null> {
        if (!imageUrl || !(imageUrl.startsWith('http://') || imageUrl.startsWith('https://'))) {
            return null;
        }

        const isLocal = imageUrl.includes("localhost") || imageUrl.includes("127.0.0.1");
        let resolvedUrl = imageUrl;

        if (process.env.PUBLIC_STORAGE_URL_SET === "true" && isLocal) {
            resolvedUrl = resolvedUrl
                .replace("localhost", "backend")
                .replace("127.0.0.1", "backend");
        }

        if (isLocal) {
            try {
                const imageResponse = await fetch(resolvedUrl);
                if (!imageResponse.ok && resolvedUrl !== imageUrl) {
                    // Fallback to original URL
                    const fallbackResponse = await fetch(imageUrl);
                    if (!fallbackResponse.ok) {
                        return null;
                    }
                    const imageBuffer = await fallbackResponse.arrayBuffer();
                    const base64 = Buffer.from(imageBuffer).toString("base64");
                    const mimeType = fallbackResponse.headers.get("content-type") || "image/png";
                    return { type: "input_image", image_url: `data:${mimeType};base64,${base64}` } as const;
                } else if (imageResponse.ok) {
                    const imageBuffer = await imageResponse.arrayBuffer();
                    const base64 = Buffer.from(imageBuffer).toString("base64");
                    const mimeType = imageResponse.headers.get("content-type") || "image/png";
                    return { type: "input_image", image_url: `data:${mimeType};base64,${base64}` } as const;
                }
            } catch {
                return null;
            }
        } else {
            return { type: "input_image", image_url: imageUrl } as const;
        }

        return null;
    }

    // Collect all image fetch tasks
    const imageFetchTasks: Promise<any | null>[] = [];

    for (const result of results || []) {
        try {
            // Use cached OCR data from fetchOcrData
            const ocrData = await fetchOcrData(result);
            if (!ocrData?.regions) continue;

            // Filter regions that are images (figures, diagrams, etc.)
            const imageRegions = ocrData.regions.filter((region: any) =>
                IMAGE_REGION_LABELS.includes(region.label?.toLowerCase())
            );

            for (const region of imageRegions) {
                // For image regions, the URL is stored in image_url field (or content field for compatibility)
                const imageUrl = (region.image_url || region.content)?.trim();
                imageFetchTasks.push(fetchRegionImage(imageUrl));
            }
        } catch {
            // Skip pages that fail to process
        }
    }

    // Parallelize all image fetches
    const fetchedImages = await Promise.all(imageFetchTasks);
    const regionImages = fetchedImages.filter(Boolean);

    if (regionImages.length === 0) {
        return [];
    }

    const labelsText = (results || [])
        .map((result, index) => `${index + 1}. ${result.label || "Unknown"}`)
        .join("\n");

    const header = {
        type: "input_text",
        text: `Based on the search results for "${query}", here are the relevant document region images (figures, tables, and diagrams):\n\n${labelsText}\n\nWhen citing these regions, use the EXACT labels provided above.`,
    } as const;

    return [header, ...regionImages];
}

