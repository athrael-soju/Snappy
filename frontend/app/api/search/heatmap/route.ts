import { NextRequest, NextResponse } from "next/server";
import { baseUrl } from "@/lib/api/client";
import { logger } from "@/lib/utils/logger";

const heatmapLogger = logger.child({ module: 'heatmap-api' });

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();

    if (!payload.query || !payload.image_url) {
      return NextResponse.json(
        { error: "query and image_url are required" },
        { status: 400 }
      );
    }

    heatmapLogger.info('Heatmap request started', {
      imageUrl: payload.image_url.substring(0, 100),
    });

    // Forward the request to the backend
    const response = await fetch(`${baseUrl}/search/heatmap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      heatmapLogger.error('Backend heatmap request failed', {
        status: response.status,
        error: errorText,
      });
      return NextResponse.json(
        { error: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    heatmapLogger.error('Heatmap API error', { error });
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
