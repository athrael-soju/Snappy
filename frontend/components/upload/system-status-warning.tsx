"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

interface SystemStatusWarningProps {
  isReady: boolean;
}

export function SystemStatusWarning({ isReady }: SystemStatusWarningProps) {
  const hasShownToast = useRef(false);
  const router = useRouter();

  useEffect(() => {
    if (!isReady && !hasShownToast.current) {
      hasShownToast.current = true;
      
      toast.warning("System Not Initialized", {
        description: "The collection and bucket must be initialized before uploading files.",
        action: {
          label: "Go to Maintenance",
          onClick: () => router.push("/maintenance"),
        },
        duration: Infinity,
      });
    }
  }, [isReady, router]);

  return null;
}
