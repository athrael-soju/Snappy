import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LucideIcon } from "lucide-react";
import type { CSSProperties, ReactNode } from "react";

type AccentKey = "primary" | "secondary" | "accent";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: ReactNode;
  href?: string;
  className?: string;
  children?: ReactNode;
  glass?: boolean;
  features?: string[];
  badges?: string[];
  accent?: AccentKey;
}

export function FeatureCard({
  icon: Icon,
  title,
  description,
  href,
  className,
  children,
  glass = false,
  features,
  badges,
  accent,
}: FeatureCardProps) {
  const accentKey: AccentKey = accent ?? "primary";
  const accentVars = {
    "--card-accent": `var(--${accentKey})`,
    "--card-accent-soft": `color-mix(in oklab, var(--${accentKey}) 16%, transparent)`,
  } as CSSProperties;

  const content = (
    <Card
      className={cn(
        "group h-full cursor-pointer rounded-[calc(var(--radius-lg)+0.5rem)] border border-border/60 bg-card/80 shadow-sm transition-all hover:-translate-y-1 hover:border-[color:var(--card-accent)] hover:shadow-lg",
        glass && "backdrop-blur-xl bg-card/75",
        className,
      )}
      style={accentVars}
    >
      <CardHeader className="flex flex-col items-center gap-3 pb-4 text-center">
        <div className="flex size-12 items-center justify-center rounded-2xl border border-border/60 bg-[color:var(--card-accent-soft)] text-[color:var(--card-accent)] shadow-sm transition-transform group-hover:scale-105">
          <Icon className="h-6 w-6" strokeWidth={2} />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground transition-colors group-hover:text-[color:var(--card-accent)]">
          {title}
        </CardTitle>
        {badges && badges.length > 0 && (
          <div className="mt-1 flex flex-wrap justify-center gap-1.5">
            {badges.map((badge, idx) => (
              <Badge key={idx} variant="secondary" className="border border-border/60 bg-card/70 px-2 py-0.5 text-xs">
                {badge}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-3.5 px-5 pb-5 text-center">
        <p className="text-sm font-medium leading-relaxed text-foreground/90">{description}</p>
        {features && features.length > 0 && (
          <ul className="space-y-2 text-left text-xs text-muted-foreground">
            {features.map((feature, idx) => (
              <li
                key={idx}
                className={cn(
                  "flex items-start gap-2",
                  idx >= 2 && "hidden sm:flex"
                )}
              >
                <span className="mt-0.5 flex-shrink-0 text-[color:var(--card-accent)]" aria-hidden="true">
                  -
                </span>
                <span className="leading-snug">{feature}</span>
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
      <a href={href} className="block h-full">
        {content}
      </a>
    );
  }

  return content;
}

