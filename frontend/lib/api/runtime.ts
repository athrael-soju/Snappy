import { z } from "zod";

import { schemas } from "@/lib/api/zod";

const searchResultsSchema = schemas.SearchItem.array();
const heatmapSchema = schemas.HeatmapResult;

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

export type HeatmapResult = {
  image_width: number;
  image_height: number;
  grid_rows: number;
  grid_columns: number;
  aggregate: string;
  min_score: number;
  max_score: number;
  heatmap: number[][];
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

export function parseHeatmapResult(data: unknown): HeatmapResult {
  const parsed = heatmapSchema.safeParse(data);
  if (!parsed.success) {
    throw new Error("Invalid heatmap response payload");
  }

  const normalizedHeatmap = parsed.data.heatmap.map((row) =>
    row.map((value) => (Number.isFinite(value) ? value : 0))
  );

  return {
    image_width: parsed.data.image_width,
    image_height: parsed.data.image_height,
    grid_rows: parsed.data.grid_rows,
    grid_columns: parsed.data.grid_columns,
    aggregate: parsed.data.aggregate.toLowerCase(),
    min_score: parsed.data.min_score,
    max_score: parsed.data.max_score,
    heatmap: normalizedHeatmap,
  };
}
