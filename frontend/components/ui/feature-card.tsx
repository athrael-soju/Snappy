import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
  features,
  badges,
}: FeatureCardProps) {
  const content = (
    <Card
      className={cn(
        "h-full cursor-pointer group transition-all border-border/50",
        glass 
          ? "bg-card/40 backdrop-blur-xl shadow-lg hover:shadow-xl hover:bg-card/50" 
          : "card-surface hover:shadow-lg",
        className
      )}
    >
      <CardHeader className="pb-4 flex flex-col items-center text-center">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary group-hover:from-primary/20 group-hover:to-primary/10 group-hover:scale-110 transition-all">
          <Icon className="h-7 w-7" strokeWidth={2} />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground mt-4 group-hover:text-primary transition-colors">
          {title}
        </CardTitle>
        {badges && badges.length > 0 && (
          <div className="flex flex-wrap gap-1.5 justify-center mt-3">
            {badges.map((badge, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs px-2 py-0.5">
                {badge}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent className="text-center px-6 pb-6 space-y-4">
        <p className="text-sm font-medium text-foreground/80 leading-relaxed">{description}</p>
        {features && features.length > 0 && (
          <ul className="text-xs space-y-2 text-left text-muted-foreground">
            {features.map((feature, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-primary mt-0.5 flex-shrink-0">✓</span>
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
