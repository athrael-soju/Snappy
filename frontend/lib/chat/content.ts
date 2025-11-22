import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import { logger } from '@/lib/utils/logger';

type DataUrl = { mime: string; base64: string };

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
            if (process.env.PUBLIC_MINIO_URL_SET === "true") {
                resolvedUrl = resolvedUrl
                    .replace("localhost", "minio")
                    .replace("127.0.0.1", "minio");
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
    const labelsText = (results || [])
        .map((result, index) => `Image ${index + 1}: ${result.label || "Unknown"}`)
        .join("\n");

    const header = {
        type: "input_text",
        text: `Based on the search results for "${query}", here are the relevant document images:\n\n${labelsText}\n\nWhen citing these images, use the EXACT labels provided above.`,
    } as const;

    const items = await Promise.all(
        (results || []).map(async (result) => {
            try {
                let imageUrl = result.image_url;
                if (!imageUrl) {
                    return null;
                }

                const isLocal = imageUrl.includes("localhost") || imageUrl.includes("127.0.0.1");
                if (process.env.PUBLIC_MINIO_URL_SET === "true") {
                    imageUrl = imageUrl.replace("localhost", "minio") || imageUrl.replace("127.0.0.1", "minio");
                }

                if (isLocal) {
                    const imageResponse = await fetch(imageUrl);
                    if (!imageResponse.ok) {
                        return null;
                    }

                    const imageBuffer = await imageResponse.arrayBuffer();
                    const base64 = Buffer.from(imageBuffer).toString("base64");
                    const mimeType = imageResponse.headers.get("content-type") || "image/png";
                    const dataUrl = `data:${mimeType};base64,${base64}`;

                    return { type: "input_image", image_url: dataUrl } as const;
                }

                return { type: "input_image", image_url: imageUrl } as const;
            } catch {
                return null;
            }
        }),
    );

    return [header, ...items.filter(Boolean)];
}

export async function buildMarkdownContent(results: SearchItem[], query: string): Promise<any[]> {
    // Build a unified text block containing all pages
    const pageContents: string[] = [];
    const IMAGE_REGION_LABELS = ['figure', 'diagram', 'image', 'chart', 'graph'];

    for (const result of results || []) {
        try {
            let pageText: string | null = null;

            // Check if OCR data is inline in payload (DuckDB mode)
            const ocrData = result.payload?.ocr;
            if (ocrData) {
                // DuckDB mode: try pre-formatted fields first
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
            } else if (result.json_url) {
                // MinIO mode: fetch from json_url (when DuckDB disabled)
                const jsonResponse = await fetch(result.json_url);
                if (jsonResponse.ok) {
                    const jsonData = await jsonResponse.json();
                    // Use the same priority as DuckDB mode
                    pageText = jsonData.markdown || jsonData.text || jsonData.raw_text || null;

                    // Inline local images in markdown if present
                    if (pageText && jsonData.markdown) {
                        pageText = await inlineLocalImages(pageText);
                    }
                }
            }

            if (pageText && pageText.trim()) {
                // Add page section with label header
                pageContents.push(`## ${result.label || "Unknown"}\n\n${pageText.trim()}`);
            }
        } catch (error) {
            logger.error('Failed to process OCR content', { error, label: result.label });
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
    const regionImages: any[] = [];

    for (const result of results || []) {
        try {
            let regions: any[] = [];
            const ocrData = result.payload?.ocr;

            if (ocrData?.regions) {
                // DuckDB mode: regions are inline
                regions = ocrData.regions;
            } else if (result.json_url) {
                // MinIO mode: fetch from json_url
                const jsonResponse = await fetch(result.json_url);
                if (jsonResponse.ok) {
                    const jsonData = await jsonResponse.json();
                    regions = jsonData.regions || [];
                }
            }

            // Filter regions that are images (figures, tables, diagrams, etc.)
            const imageRegions = regions.filter((region: any) =>
                IMAGE_REGION_LABELS.includes(region.label?.toLowerCase())
            );

            for (const region of imageRegions) {
                // For image regions, the URL is stored in the content field
                const imageUrl = region.content?.trim();

                if (!imageUrl || !(imageUrl.startsWith('http://') || imageUrl.startsWith('https://'))) {
                    continue;
                }

                const isLocal = imageUrl.includes("localhost") || imageUrl.includes("127.0.0.1");
                let resolvedUrl = imageUrl;

                if (process.env.PUBLIC_MINIO_URL_SET === "true" && isLocal) {
                    resolvedUrl = resolvedUrl
                        .replace("localhost", "minio")
                        .replace("127.0.0.1", "minio");
                }

                if (isLocal) {
                    try {
                        const imageResponse = await fetch(resolvedUrl);
                        if (!imageResponse.ok && resolvedUrl !== imageUrl) {
                            // Fallback to original URL
                            const fallbackResponse = await fetch(imageUrl);
                            if (!fallbackResponse.ok) {
                                continue;
                            }
                            const imageBuffer = await fallbackResponse.arrayBuffer();
                            const base64 = Buffer.from(imageBuffer).toString("base64");
                            const mimeType = fallbackResponse.headers.get("content-type") || "image/png";
                            const dataUrl = `data:${mimeType};base64,${base64}`;
                            regionImages.push({ type: "input_image", image_url: dataUrl } as const);
                        } else if (imageResponse.ok) {
                            const imageBuffer = await imageResponse.arrayBuffer();
                            const base64 = Buffer.from(imageBuffer).toString("base64");
                            const mimeType = imageResponse.headers.get("content-type") || "image/png";
                            const dataUrl = `data:${mimeType};base64,${base64}`;
                            regionImages.push({ type: "input_image", image_url: dataUrl } as const);
                        }
                    } catch {
                        // Skip images that fail to fetch
                    }
                } else {
                    regionImages.push({ type: "input_image", image_url: imageUrl } as const);
                }
            }
        } catch {
            // Skip pages that fail to process
        }
    }

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

