import { z } from "zod";
import { logger } from '@/lib/utils/logger';
import { schemas } from "@/lib/api/schemas";
import type { SearchItem } from "@/lib/api/generated/models/SearchItem";

const searchResultsSchema = schemas.SearchItem.array();

export type SearchPayload = {
  filename?: string;
  pdf_page_index?: number;
  [key: string]: unknown;
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
        json_url:
          typeof item.json_url === "string" || item.json_url === null || typeof item.json_url === "undefined"
            ? item.json_url ?? null
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
