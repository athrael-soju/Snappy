"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Settings } from "lucide-react";
import { useSystemStatus } from "@/stores/app-store";

/**
 * Component that shows a toast notification when the system is not ready.
 * Prompts the user to configure the system via the maintenance page.
 * Toast persists until manually dismissed or system becomes ready.
 */
export function SystemStatusToast() {
  const { isReady } = useSystemStatus();
  const router = useRouter();
  const toastIdRef = useRef<string | number | null>(null);

  useEffect(() => {
    // Show toast when system is not ready
    if (!isReady && toastIdRef.current === null) {
      toastIdRef.current = toast.warning("System Configuration Required", {
        description: "Please configure the system before using the services.",
        duration: Infinity, // Toast stays until dismissed or system is ready
        action: {
          label: "Go to Maintenance",
          onClick: () => router.push("/maintenance"),
        },
        icon: <Settings className="size-4" />,
      });
    }

    // Dismiss toast when system becomes ready
    if (isReady && toastIdRef.current !== null) {
      toast.dismiss(toastIdRef.current);
      toastIdRef.current = null;
    }
  }, [isReady, router]);

  return null; // This component doesn't render anything
}
