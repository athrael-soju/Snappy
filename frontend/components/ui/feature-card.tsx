import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { GlassDepth } from "@/components/ui/glass-panel";
import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: ReactNode;
  href?: string;
  className?: string;
  children?: ReactNode;
  glass?: boolean;
  glassDepth?: GlassDepth;
  features?: string[];
  badges?: string[];
}

export function FeatureCard({
  icon: Icon,
  title,
  description,
  href,
  className,
  children,
  glass = false,
  glassDepth = "surface",
  features,
  badges,
}: FeatureCardProps) {
  const isInteractive = Boolean(href);

  const content = (
    <Card
      data-glass-depth={glass ? glassDepth : undefined}
      className={cn(
        "group relative h-full transition-transform duration-200 ease-out",
        isInteractive && "cursor-pointer",
        glass ? "glass-surface" : "card-surface",
        className
      )}
    >
      <CardHeader className="flex flex-col items-center pb-4 text-center">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/15 via-primary/10 to-primary/5 text-primary shadow-[0_18px_28px_-18px_rgba(79,70,229,0.55)] transition-transform duration-200 group-hover:scale-110">
          <Icon className="h-7 w-7 drop-shadow-[0_2px_4px_rgba(79,70,229,0.35)]" strokeWidth={2} />
        </div>
        <CardTitle className="mt-4 text-lg font-semibold text-foreground transition-colors duration-200 group-hover:text-primary drop-shadow-[0_1px_1px_rgba(15,23,42,0.22)] dark:drop-shadow-[0_1px_1px_rgba(2,6,23,0.55)]">
          {title}
        </CardTitle>
        {badges && badges.length > 0 && (
          <div className="mt-3 flex flex-wrap justify-center gap-1.5">
            {badges.map((badge, idx) => (
              <Badge key={idx} variant="secondary" className="px-2 py-0.5 text-xs">
                {badge}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-4 px-6 pb-6 text-center">
        <p className="text-sm font-medium leading-relaxed text-foreground/90 drop-shadow-[0_1px_1px_rgba(15,23,42,0.15)] dark:text-foreground/85 dark:drop-shadow-[0_1px_1px_rgba(2,6,23,0.5)]">
          {description}
        </p>
        {features && features.length > 0 && (
          <ul className="space-y-2 text-left text-sm text-muted-foreground/90">
            {features.map((feature, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs leading-snug sm:text-sm">
                <span className="mt-0.5 flex-shrink-0 text-primary/85">&bull;</span>
                <span className="leading-snug text-foreground/80 dark:text-foreground/75">{feature}</span>
              </li>
            ))}
          </ul>
        )}
        {children}
      </CardContent>
    </Card>
  );

  if (href) {
    return (
      <a
        href={href}
        className="block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background/0"
      >
        {content}
      </a>
    );
  }

  return content;
}
