import { useMemo, useState, useCallback, ReactNode } from 'react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { AppButton } from '@/components/app-button';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { ExternalLink } from 'lucide-react';

type CitationHoverCardProps = {
  number: number;
  imageUrl: string;
  label: string;
  score?: number | null;
  onOpen?: () => void;
  children?: ReactNode;
};

/**
 * Renders a citation with preview popover on hover/focus.
 * If children are provided, they will be used as the trigger, otherwise a numbered badge is shown.
 */
export default function CitationHoverCard({
  number,
  imageUrl,
  label,
  score,
  onOpen,
  children,
}: CitationHoverCardProps) {
  const [open, setOpen] = useState(false);

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
