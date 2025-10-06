"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

export function ThemeSwitch() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const isDarkMode = resolvedTheme === "dark";

  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="theme-switch" className="sr-only">
        Toggle theme
      </Label>
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border/50 bg-card/80 shadow-sm">
        <Sun className={cn("w-4 h-4 transition-colors", isDarkMode ? "text-muted-foreground" : "text-amber-500")} />
        <Switch
          id="theme-switch"
          checked={isDarkMode}
          onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
          aria-label="Toggle theme"
        />
        <Moon className={cn("w-4 h-4 transition-colors", isDarkMode ? "text-blue-400" : "text-muted-foreground")} />
      </div>
    </div>
  );
}
