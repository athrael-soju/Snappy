import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, ExternalLink } from "lucide-react";
import Link from "next/link";

interface SystemStatusWarningProps {
  isReady: boolean;
}

export function SystemStatusWarning({ isReady }: SystemStatusWarningProps) {
  if (isReady) return null;

  return (
    <Alert className="border-amber-300 bg-amber-50">
      <AlertTriangle className="h-5 w-5 text-amber-600" />
      <AlertTitle className="text-amber-900 font-semibold">System Not Initialized</AlertTitle>
      <AlertDescription className="text-amber-800">
        The collection and bucket must be initialized before uploading files.
        <Link href="/maintenance?section=data" className="inline-flex items-center gap-1 ml-2 text-amber-900 font-medium underline hover:text-amber-950">
          Go to Maintenance
          <ExternalLink className="w-3 h-3" />
        </Link>
      </AlertDescription>
    </Alert>
  );
}
