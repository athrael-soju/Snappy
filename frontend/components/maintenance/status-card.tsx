import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Loader2, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassPanel } from "@/components/ui/glass-panel";
import type { CollectionStatus, BucketStatus } from "./types";

type AccentColor = "blue" | "orange";

const accentStyles: Record<AccentColor, {
  cardBorder: string;
  divider: string;
  loader: string;
  bullet: string;
  iconBorder: string;
}> = {
  blue: {
    cardBorder: "border-blue-200/70 dark:border-blue-900/60",
    divider: "border-blue-200/60 dark:border-blue-900/50",
    loader: "text-blue-500",
    bullet: "bg-blue-500",
    iconBorder: "border-blue-200/70 dark:border-blue-900/60",
  },
  orange: {
    cardBorder: "border-orange-200/70 dark:border-orange-900/60",
    divider: "border-orange-200/60 dark:border-orange-900/50",
    loader: "text-orange-500",
    bullet: "bg-orange-500",
    iconBorder: "border-orange-200/70 dark:border-orange-900/60",
  },
};

interface StatusCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
  accentColor: AccentColor;
  isLoading: boolean;
  status: CollectionStatus | BucketStatus | null;
  exists?: boolean;
  details: React.ReactNode;
  features: string[];
}

export function StatusCard({
  title,
  description,
  icon: Icon,
  iconColor,
  iconBg,
  accentColor,
  isLoading,
  status,
  exists,
  details,
  features,
}: StatusCardProps) {
  const accent = accentStyles[accentColor] ?? accentStyles.blue;

  return (
    <GlassPanel className={cn("transition-shadow hover:shadow-lg p-6")}>
      <CardHeader className="pb-3 px-0 pt-0">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("rounded-xl border p-2", iconBg, accent.iconBorder)}>
              <Icon className={cn("h-5 w-5", iconColor)} />
            </div>
            <div>
              <CardTitle className="text-base font-semibold text-foreground">{title}</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">{description}</CardDescription>
            </div>
          </div>
          {status && (
            exists ? (
              <Badge className="border-green-300 bg-green-100 text-green-700">
                <CheckCircle2 className="mr-1 h-3 w-3" />
                Active
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-gray-100 text-gray-700">
                <XCircle className="mr-1 h-3 w-3" />
                Not Found
              </Badge>
            )
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 px-0 pb-0">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className={cn("h-6 w-6 animate-spin", accent.loader)} />
          </div>
        ) : status ? (
          <>
            {details}
            {status.error && (
              <div className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
                Error: {status.error}
              </div>
            )}
            <div className={cn("mt-3 space-y-2 border-t pt-3 text-xs", accent.divider)}>
              {features.map((feature, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className={cn("mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full", accent.bullet)} />
                  <span className="text-muted-foreground">{feature}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="text-sm text-muted-foreground">No status available</p>
        )}
      </CardContent>
    </GlassPanel>
  );
}
