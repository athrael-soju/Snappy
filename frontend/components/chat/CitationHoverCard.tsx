import { useMemo, useState, useCallback, ReactNode } from 'react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { AppButton } from '@/components/app-button';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { ExternalLink, Flame, Loader2 } from 'lucide-react';
import { fetchHeatmap } from '@/lib/api/chat';

type CitationHoverCardProps = {
  number: number;
  imageUrl: string;
  label: string;
  score?: number | null;
  query?: string | null;
  heatmapsEnabled?: boolean;
  onOpen?: () => void;
  children?: ReactNode;
};

/**
 * Renders a citation with preview popover on hover/focus.
 * If children are provided, they will be used as the trigger, otherwise a numbered badge is shown.
 * When heatmapsEnabled is true and query is provided, shows a toggle to fetch and view attention heatmaps.
 */
export default function CitationHoverCard({
  number,
  imageUrl,
  label,
  score,
  query,
  heatmapsEnabled = false,
  onOpen,
  children,
}: CitationHoverCardProps) {
  const [open, setOpen] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapUrl, setHeatmapUrl] = useState<string | null>(null);
  const [isLoadingHeatmap, setIsLoadingHeatmap] = useState(false);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);

  const scoreBadge = useMemo(() => {
    if (typeof score !== 'number') return null;
    return (
      <Badge variant="secondary" className="rounded-full px-2 py-0.5 text-body-xs font-semibold">
        {score.toFixed(2)}
      </Badge>
    );
  }, [score]);

  const handleMouseEnter = useCallback(() => setOpen(true), []);
  const handleActivate = useCallback(() => {
    onOpen?.();
    setOpen(false);
  }, [onOpen]);

  const handleHeatmapToggle = useCallback(async () => {
    // If turning off heatmap, just toggle
    if (showHeatmap) {
      setShowHeatmap(false);
      return;
    }

    // If we already have the heatmap cached, just show it
    if (heatmapUrl) {
      setShowHeatmap(true);
      return;
    }

    // Fetch the heatmap
    if (!query) {
      setHeatmapError('Query not available');
      return;
    }

    setIsLoadingHeatmap(true);
    setHeatmapError(null);

    try {
      const result = await fetchHeatmap(query, imageUrl);
      setHeatmapUrl(result.heatmap_url);
      setShowHeatmap(true);
    } catch (error) {
      setHeatmapError(error instanceof Error ? error.message : 'Failed to load heatmap');
    } finally {
      setIsLoadingHeatmap(false);
    }
  }, [showHeatmap, heatmapUrl, query, imageUrl]);

  // Determine which image to show
  const displayImageUrl = showHeatmap && heatmapUrl ? heatmapUrl : imageUrl;

  // Show heatmap toggle only when heatmaps are enabled and we have a query
  const canShowHeatmap = heatmapsEnabled && query;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        {children ? (
          <span onMouseEnter={handleMouseEnter} onFocus={handleMouseEnter}>
            {children}
          </span>
        ) : (
          <span className="ml-1 align-super">
            <AppButton
              type="button"
              variant="link"
              size="inline"
              aria-label={`View citation ${number}`}
              onMouseEnter={handleMouseEnter}
              onFocus={handleMouseEnter}
            >
              [{number}]
            </AppButton>
          </span>
        )}
      </PopoverTrigger>
      <PopoverContent side="top" align="start" className="w-64 space-y-3">
        <div className="space-y-2 text-body-sm">
          <p className="font-semibold leading-tight">{label}</p>
          <div className="flex items-center gap-2 text-body-xs text-muted-foreground">
            <Badge variant="outline" className="rounded-full px-2 py-0.5 text-body-xs uppercase tracking-wide">
              Citation {number}
            </Badge>
            {scoreBadge}
            {canShowHeatmap && (
              <Badge
                variant={showHeatmap ? 'default' : 'outline'}
                className="rounded-full px-2 py-0.5 text-body-xs cursor-pointer"
                onClick={handleHeatmapToggle}
              >
                {isLoadingHeatmap ? (
                  <Loader2 className="size-icon-3xs mr-1 animate-spin" />
                ) : (
                  <Flame className="size-icon-3xs mr-1" />
                )}
                Heatmap
              </Badge>
            )}
          </div>
          {heatmapError && (
            <p className="text-destructive text-body-xs">{heatmapError}</p>
          )}
        </div>
        <div className="relative h-32 w-full overflow-hidden rounded-md border">
          {isLoadingHeatmap && (
            <div className="absolute inset-0 flex items-center justify-center bg-muted/50 z-10">
              <Loader2 className="size-icon-md animate-spin text-muted-foreground" />
            </div>
          )}
          {/* Use img tag for data URLs (heatmaps), Next Image for remote URLs */}
          {displayImageUrl.startsWith('data:') ? (
            <img
              src={displayImageUrl}
              alt={label}
              className="h-full w-full object-cover"
            />
          ) : (
            <Image
              src={displayImageUrl}
              alt={label}
              fill
              sizes="256px"
              className="object-cover"
              priority={false}
            />
          )}
        </div>
        <AppButton
          type="button"
          size="sm"
          variant="outline"
          fullWidth
          onClick={handleActivate}
        >
          <ExternalLink className="size-icon-xs" />
          View page
        </AppButton>
      </PopoverContent>
    </Popover>
  );
}
