import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Loader2, LucideIcon, Ban } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CollectionStatus, BucketStatus } from "./types";

type AccentColor = "blue" | "orange";

const accentStyles: Record<AccentColor, {
  loader: string;
  bullet: string;
}> = {
  blue: {
    loader: "text-blue-500",
    bullet: "bg-blue-500",
  },
  orange: {
    loader: "text-orange-500",
    bullet: "bg-orange-500",
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
  const isDisabled = !!(status && "disabled" in status && (status as BucketStatus).disabled);

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("rounded-lg border p-2", iconBg)}>
              <Icon className={cn("h-5 w-5", iconColor)} />
            </div>
            <div>
              <CardTitle className="text-base font-semibold text-foreground">{title}</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">{description}</CardDescription>
            </div>
          </div>
          {status && (
            isDisabled ? (
              <Badge className="bg-blue-100 text-blue-700">
                <Ban className="mr-1 h-3 w-3" />
                Disabled
              </Badge>
            ) : exists ? (
              <Badge className="bg-green-100 text-green-700">
                <CheckCircle2 className="mr-1 h-3 w-3" />
                Active
              </Badge>
            ) : (
              <Badge variant="secondary">
                <XCircle className="mr-1 h-3 w-3" />
                Not found
              </Badge>
            )
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className={cn("h-6 w-6 animate-spin", accent.loader)} />
          </div>
        ) : status ? (
          <>
            {details}
            {status.error && !isDisabled && (
              <div className="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
                Error: {status.error}
              </div>
            )}
            <div className="mt-3 space-y-2 border-t pt-3 text-xs">
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
    </Card>
  );
}
