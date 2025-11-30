"use client";

import { useEffect, useRef, useState } from "react";
import chroma from "chroma-js";
import {
  normalizeValues,
  type NormalizationStrategy,
} from "@/lib/utils/normalization";

export type TokenSimilarityMap = {
  token: string;
  token_index: number;
  similarity_map: number[][];
};

export type InterpretabilityData = {
  query: string;
  tokens: string[];
  similarity_maps: TokenSimilarityMap[];
  n_patches_x: number;
  n_patches_y: number;
  image_width: number;
  image_height: number;
};

export type ColorScale =
  | "Spectral"
  | "RdYlBu"
  | "RdBu"
  | "YlOrRd"
  | "YlGnBu"
  | "Reds"
  | "Blues"
  | "Oranges"
  | "Purples";

export type InterpretabilityHeatmapProps = {
  data: InterpretabilityData;
  imageWidth: number;
  imageHeight: number;
  selectedToken?: number;
  opacity?: number;
  colorScale?: ColorScale;
  normalizationStrategy?: NormalizationStrategy;
};

/**
 * Get a ColorBrewer scale from chroma-js
 * Diverging scales (for comparing high/low):
 * - Spectral: Multi-hue diverging
 * - RdYlBu: Red-Yellow-Blue diverging
 * - RdBu: Red-Blue diverging
 *
 * Sequential scales (for intensity):
 * - YlOrRd: Yellow-Orange-Red
 * - YlGnBu: Yellow-Green-Blue
 * - Reds: White to red
 * - Blues: White to blue
 * - Oranges: White to orange
 * - Purples: White to purple
 */
function getColorScale(scale: ColorScale): chroma.Scale {
  return chroma.scale(chroma.brewer[scale]);
}

export function InterpretabilityHeatmap({
  data,
  imageWidth,
  imageHeight,
  selectedToken,
  opacity = 0.7,
  colorScale = "YlOrRd",
  normalizationStrategy = "minmax",
}: InterpretabilityHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredToken, setHoveredToken] = useState<number | null>(null);

  const activeToken = selectedToken ?? hoveredToken ?? null;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, imageWidth, imageHeight);

    if (activeToken === null || activeToken === undefined) return;

    const tokenMap = data.similarity_maps[activeToken];
    if (!tokenMap) return;

    const simMap = tokenMap.similarity_map;

    // Flatten similarity values for normalization
    const allValues = simMap.flat();

    // Get normalization bounds
    const { min, max } = normalizeValues(allValues, normalizationStrategy);

    // Get the color scale
    const scale = getColorScale(colorScale);

    // Create temporary canvas at patch resolution for smooth upscaling
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = data.n_patches_x;
    tempCanvas.height = data.n_patches_y;
    const tempCtx = tempCanvas.getContext("2d");
    if (!tempCtx) return;

    const imageData = tempCtx.createImageData(data.n_patches_x, data.n_patches_y);
    const pixels = imageData.data;

    for (let x = 0; x < data.n_patches_x; x++) {
      for (let y = 0; y < data.n_patches_y; y++) {
        const value = simMap[x][y];
        const normalized = max > min ? (value - min) / (max - min) : 0;
        const [r, g, b] = scale(normalized).rgb();

        const idx = (y * data.n_patches_x + x) * 4;
        pixels[idx] = Math.round(r);
        pixels[idx + 1] = Math.round(g);
        pixels[idx + 2] = Math.round(b);
        pixels[idx + 3] = Math.round(opacity * 255);
      }
    }

    tempCtx.putImageData(imageData, 0, 0);

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(tempCanvas, 0, 0, imageWidth, imageHeight);
  }, [data, imageWidth, imageHeight, activeToken, opacity, colorScale, normalizationStrategy]);

  return (
    <canvas
      ref={canvasRef}
      width={imageWidth}
      height={imageHeight}
      className="absolute top-0 left-0 pointer-events-none"
      style={{
        width: `${imageWidth}px`,
        height: `${imageHeight}px`,
        mixBlendMode: "multiply",
        opacity: activeToken !== null ? 1 : 0,
        transition: "opacity 0.2s ease-in-out",
        zIndex: 10
      }}
    />
  );
}

