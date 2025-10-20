"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Settings } from "lucide-react";
import { useSystemStatus } from "@/stores/app-store";

/**
 * Component that shows a toast notification when the system is not ready.
 * Prompts the user to configure the system via the maintenance page.
 */
export function SystemStatusToast() {
  const { isReady } = useSystemStatus();
  const router = useRouter();
  const hasShownToast = useRef(false);

  useEffect(() => {
    // Only show toast once per session when system is not ready
    if (!isReady && !hasShownToast.current) {
      hasShownToast.current = true;
      
      toast.warning("System Configuration Required", {
        description: "Please configure the system before using the services.",
        duration: 10000, // Show for 10 seconds
        action: {
          label: "Go to Maintenance",
          onClick: () => router.push("/maintenance"),
        },
        icon: <Settings className="size-4" />,
      });
    }

    // Reset the flag when system becomes ready
    if (isReady) {
      hasShownToast.current = false;
    }
  }, [isReady, router]);

  return null; // This component doesn't render anything
}
