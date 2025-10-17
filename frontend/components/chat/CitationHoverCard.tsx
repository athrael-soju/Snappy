import { useMemo, useState, useCallback } from 'react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { ExternalLink } from 'lucide-react';

type CitationHoverCardProps = {
  number: number;
  imageUrl: string;
  label: string;
  score?: number | null;
  onOpen?: () => void;
};

/**
 * Renders a superscript citation indicator that shows a preview popover on hover/focus.
 */
export default function CitationHoverCard({
  number,
  imageUrl,
  label,
  score,
  onOpen,
}: CitationHoverCardProps) {
  const [open, setOpen] = useState(false);

  const scoreBadge = useMemo(() => {
    if (typeof score !== 'number') return null;
    const percentage = score > 1 ? score : score * 100;
    const cappedPercentage = Math.min(100, percentage);
    return (
      <Badge variant="secondary" className="rounded-full px-2 py-0.5 text-[10px] font-semibold">
        {cappedPercentage.toFixed(3)}%
      </Badge>
    );
  }, [score]);

  const handleMouseEnter = useCallback(() => setOpen(true), []);
  const handleActivate = useCallback(() => {
    onOpen?.();
    setOpen(false);
  }, [onOpen]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="ml-1 align-super text-xs font-semibold text-blue-600 hover:text-blue-500 focus-visible:outline-none focus-visible:underline"
          aria-label={`View citation ${number}`}
          onMouseEnter={handleMouseEnter}
          onFocus={handleMouseEnter}
        >
          [{number}]
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 space-y-3">
        <div className="space-y-2 text-sm">
          <p className="font-semibold leading-tight">{label}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline" className="rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide">
              Citation {number}
            </Badge>
            {scoreBadge}
          </div>
        </div>
        <div className="relative h-32 w-full overflow-hidden rounded-md border">
          <Image
            src={imageUrl}
            alt={label}
            fill
            sizes="256px"
            className="object-cover"
            priority={false}
          />
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="w-full gap-2"
          onClick={handleActivate}
        >
          <ExternalLink className="h-4 w-4" />
          View page
        </Button>
      </PopoverContent>
    </Popover>
  );
}
