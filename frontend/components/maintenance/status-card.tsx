import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, XCircle, Loader2, LucideIcon } from "lucide-react";
import type { CollectionStatus, BucketStatus } from "./types";

interface StatusCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
  accentColor: string;
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
  return (
    <Card className={`border ${accentColor}-200/50 bg-gradient-to-br from-${accentColor}-500/5 to-${accentColor === 'blue' ? 'cyan' : 'amber'}-500/5`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl ${iconBg} border-2 ${accentColor}-200/50`}>
              <Icon className={`w-5 h-5 ${iconColor}`} />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">{title}</CardTitle>
              <CardDescription className="text-xs">{description}</CardDescription>
            </div>
          </div>
          {status && (
            exists ? (
              <Badge className="bg-green-100 text-green-700 border-green-300">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Active
              </Badge>
            ) : (
              <Badge variant="secondary" className="bg-gray-100 text-gray-700">
                <XCircle className="w-3 h-3 mr-1" />
                Not Found
              </Badge>
            )
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className={`w-6 h-6 animate-spin text-${accentColor}-500`} />
          </div>
        ) : status ? (
          <>
            {details}
            {status.error && (
              <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                Error: {status.error}
              </div>
            )}
            <div className={`mt-3 pt-3 border-t border-${accentColor}-200/30 space-y-2 text-xs`}>
              {features.map((feature, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className={`w-1.5 h-1.5 bg-${accentColor}-500 rounded-full mt-1 flex-shrink-0`}></div>
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
