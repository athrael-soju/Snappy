import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: ReactNode;
  href?: string;
  className?: string;
  children?: ReactNode;
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
  features,
  badges,
}: FeatureCardProps) {
  const content = (
    <Card
      className={cn(
        "h-full cursor-pointer transition hover:shadow-md",
        className
      )}
    >
      <CardHeader className="flex flex-col items-center pb-4 text-center">
        <div className="mb-3 inline-flex size-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-6 w-6" strokeWidth={2} />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground">
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
        <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
        {features && features.length > 0 && (
          <ul className="space-y-2 text-left text-xs text-muted-foreground">
            {features.map((feature, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <Check className="mt-0.5 h-3.5 w-3.5 text-primary" strokeWidth={3} />
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
