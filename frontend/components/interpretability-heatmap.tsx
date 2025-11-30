"use client";

import { useEffect, useRef, useState } from "react";

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

export type InterpretabilityHeatmapProps = {
  data: InterpretabilityData;
  imageWidth: number;
  imageHeight: number;
  selectedToken?: number;
  opacity?: number;
};

export function InterpretabilityHeatmap({
  data,
  imageWidth,
  imageHeight,
  selectedToken,
  opacity = 0.75,
}: InterpretabilityHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredToken, setHoveredToken] = useState<number | null>(null);

  const activeToken = selectedToken ?? hoveredToken ?? null;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas first
    ctx.clearRect(0, 0, imageWidth, imageHeight);

    // If no token selected, don't draw anything
    if (activeToken === null || activeToken === undefined) return;

    // Get the similarity map for the active token
    const tokenMap = data.similarity_maps[activeToken];
    if (!tokenMap) return;

    const simMap = tokenMap.similarity_map;

    // Collect all values for percentile-based normalization
    const allValues: number[] = [];
    for (const row of simMap) {
      for (const val of row) {
        allValues.push(val);
      }
    }
    allValues.sort((a, b) => a - b);

    // Use 5th and 95th percentile for better contrast
    const p5Index = Math.floor(allValues.length * 0.05);
    const p95Index = Math.floor(allValues.length * 0.95);
    const min = allValues[p5Index];
    const max = allValues[p95Index];

    // Create a temporary canvas at patch resolution for smooth upscaling
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = data.n_patches_x;
    tempCanvas.height = data.n_patches_y;
    const tempCtx = tempCanvas.getContext('2d');
    if (!tempCtx) return;

    // Draw heatmap at patch resolution (1 pixel = 1 patch)
    const imageData = tempCtx.createImageData(data.n_patches_x, data.n_patches_y);
    const pixels = imageData.data;

    for (let x = 0; x < data.n_patches_x; x++) {
      for (let y = 0; y < data.n_patches_y; y++) {
        const value = simMap[x][y];
        const normalized = max > min ? (value - min) / (max - min) : 0;

        // Color mapping: blue (low) -> white (mid) -> red (high)
        const r = normalized < 0.5
          ? Math.round(255 * (normalized * 2))
          : 255;
        const g = normalized < 0.5
          ? Math.round(255 * (normalized * 2))
          : Math.round(255 * (1 - (normalized - 0.5) * 2));
        const b = normalized < 0.5
          ? 255
          : Math.round(255 * (1 - (normalized - 0.5) * 2));

        // Calculate pixel index (note: y is row, x is column)
        const idx = (y * data.n_patches_x + x) * 4;
        pixels[idx] = r;
        pixels[idx + 1] = g;
        pixels[idx + 2] = b;
        pixels[idx + 3] = Math.round(opacity * 255);
      }
    }

    tempCtx.putImageData(imageData, 0, 0);

    // Draw scaled up to main canvas with smoothing enabled
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(tempCanvas, 0, 0, imageWidth, imageHeight);
  }, [data, imageWidth, imageHeight, activeToken, opacity]);

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

export type TokenSelectorProps = {
  tokens: string[];
  selectedToken: number | null;
  onTokenSelect: (index: number | null) => void;
};

export function TokenSelector({
  tokens,
  selectedToken,
  onTokenSelect,
}: TokenSelectorProps) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {tokens.map((token, idx) => (
        <button
          key={idx}
          onClick={() => onTokenSelect(selectedToken === idx ? null : idx)}
          className={`px-2 py-0.5 rounded text-xs transition-all ${
            selectedToken === idx
              ? "bg-primary text-primary-foreground"
              : "bg-secondary/60 text-secondary-foreground hover:bg-secondary"
          }`}
        >
          {token}
        </button>
      ))}
    </div>
  );
}
