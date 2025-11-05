import type { SearchItem } from "@/lib/api/generated/models/SearchItem";

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
    const labelsText = (results || [])
        .map((result, index) => `Document ${index + 1}: ${result.label || "Unknown"}`)
        .join("\n");

    const header = {
        type: "input_text",
        text: `Based on the search results for "${query}", here are the relevant document contents:\n\n${labelsText}\n\nWhen citing these documents, use the EXACT labels provided above.`,
    } as const;

    const items = await Promise.all(
        (results || []).map(async (result) => {
            try {
                const jsonUrl = result.json_url;
                if (!jsonUrl) {
                    return null;
                }

                const jsonResponse = await fetch(jsonUrl);
                if (!jsonResponse.ok) {
                    return null;
                }

                const jsonData = await jsonResponse.json();
                let markdown = jsonData.markdown;
                if (!markdown) {
                    return null;
                }

                markdown = await inlineLocalImages(markdown);

                return {
                    type: "input_text",
                    text: `[${result.label || "Unknown"}]\n${markdown}`,
                } as const;
            } catch (error) {
                console.error("Failed to fetch markdown:", error);
                return null;
            }
        }),
    );

    return [header, ...items.filter(Boolean)];
}

export function appendUserImages(input: any[], imageContent: any[]) {
    input.push({
        role: "user",
        content: imageContent,
    } as any);
}

export function appendCitationReminder(input: any[], results: SearchItem[] | null) {
    if (!results || results.length === 0) {
        return;
    }

    const labelLines = results
        .map((result, index) => (result.label ? `${index + 1}. ${result.label}` : null))
        .filter(Boolean)
        .join("\n");

    const reminderSections = [
        "Use only the retrieved document images to answer.",
        "Every factual statement must include an inline citation using one of the exact labels provided.",
        "If a statement cannot be supported by these labels, omit it or explain that no supporting evidence was found.",
    ];

    if (labelLines) {
        reminderSections.push("Available citation labels:\n" + labelLines);
    }

    input.push({
        role: "system",
        content: [{ type: "input_text", text: reminderSections.join("\n") }],
    } as any);
}
