import { z } from "zod";

import { schemas } from "@/lib/api/zod";

const searchResultsSchema = schemas.SearchItem.array();

export type SearchPayload = {
  filename?: string;
  pdf_page_index?: number;
  [key: string]: unknown;
};

export type SearchItem = {
  image_url: string | null;
  label: string | null;
  payload: SearchPayload;
  score?: number | null;
};

export function parseSearchResults(data: unknown): SearchItem[] {
  const parsed = searchResultsSchema.safeParse(data);
  if (parsed.success) {
    return parsed.data.map((item) => {
      const rawPayload = item.payload;
      const payload: SearchPayload = {};

      if (rawPayload && typeof rawPayload === "object") {
        for (const [key, value] of Object.entries(rawPayload)) {
          if (key === "filename" && typeof value === "string") {
            payload.filename = value;
          } else if (key === "pdf_page_index" && typeof value === "number") {
            payload.pdf_page_index = value;
          } else {
            payload[key] = value;
          }
        }
      }

      return {
        image_url:
          typeof item.image_url === "string" || item.image_url === null
            ? item.image_url
            : null,
        label:
          typeof item.label === "string" || item.label === null
            ? item.label
            : null,
        score:
          typeof item.score === "number" || item.score === null || typeof item.score === "undefined"
            ? item.score ?? null
            : null,
        payload,
      };
    });
  }

  console.warn("Invalid search response payload", parsed.error);
  return [];
}

export function parseKnowledgeBaseItems(data: unknown): SearchItem[] {
  return parseSearchResults(data);
}
