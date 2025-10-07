import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: ReactNode;
  href?: string;
  className?: string;
  children?: ReactNode;
}

export function FeatureCard({
  icon: Icon,
  title,
  description,
  href,
  className,
  children,
}: FeatureCardProps) {
  const content = (
    <Card
      className={cn(
        "card-surface h-full min-h-[200px] cursor-pointer group transition-all hover:shadow-lg border-border/50",
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
      </CardHeader>
      <CardContent className="text-sm leading-relaxed text-muted-foreground text-center px-4">
        {description}
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
