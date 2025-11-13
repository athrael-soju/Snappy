"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { AppButton } from "@/components/app-button";
import { logger } from "@/lib/utils/logger";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to the console and logger
    logger.error("Error boundary caught error", {
      error: error.message,
      digest: error.digest,
      stack: error.stack,
    });
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="mx-auto w-full max-w-md space-y-6 rounded-2xl border border-destructive/40 bg-card p-8 text-center shadow-xl">
        <div className="flex justify-center">
          <div className="rounded-full bg-destructive/10 p-4">
            <AlertCircle className="size-12 text-destructive" />
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-heading-lg font-semibold text-foreground">
            Something went wrong
          </h1>
          <p className="text-body text-muted-foreground">
            An unexpected error occurred while loading this page.
          </p>
        </div>

        {error.message && (
          <div className="rounded-lg border border-border bg-muted/50 p-4">
            <p className="text-body-sm font-mono text-left text-foreground/80 break-words">
              {error.message}
            </p>
          </div>
        )}

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <AppButton
            onClick={reset}
            variant="hero"
          >
            <div className="flex items-center gap-2">
              <RefreshCw className="size-icon-sm" />
              Try again
            </div>
          </AppButton>
          <AppButton
            onClick={() => window.location.href = "/"}
            variant="outline"
          >
            Go home
          </AppButton>
        </div>

        {error.digest && (
          <p className="text-body-xs text-muted-foreground">
            Error ID: {error.digest}
          </p>
        )}
      </div>
    </div>
  );
}
