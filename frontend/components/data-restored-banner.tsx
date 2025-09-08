"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { RotateCcw, X } from "lucide-react";

interface DataRestoredBannerProps {
  dataType: "search" | "chat" | "upload";
  description: string;
  onClear?: () => void;
  showClearButton?: boolean;
}

export function DataRestoredBanner({ 
  dataType, 
  description, 
  onClear, 
  showClearButton = true 
}: DataRestoredBannerProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Auto-hide after 5 seconds
    const timer = setTimeout(() => {
      setIsVisible(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  const getColors = () => {
    switch (dataType) {
      case "search":
        return "border-blue-200 bg-blue-50/50 text-blue-800";
      case "chat":
        return "border-purple-200 bg-purple-50/50 text-purple-800";
      case "upload":
        return "border-green-200 bg-green-50/50 text-green-800";
      default:
        return "border-muted bg-muted/50 text-foreground";
    }
  };

  const handleClear = () => {
    setIsVisible(false);
    onClear?.();
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.95 }}
          transition={{ duration: 0.3 }}
          className="mb-4"
        >
          <Alert className={`${getColors()} border-2`}>
            <RotateCcw className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>{description}</span>
              <div className="flex items-center gap-2 ml-4">
                {showClearButton && onClear && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClear}
                    className="h-6 px-2 text-xs hover:bg-white/60"
                  >
                    Clear
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsVisible(false)}
                  className="h-6 w-6 hover:bg-white/60"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
