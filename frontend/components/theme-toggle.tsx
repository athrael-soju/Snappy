"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/8bit/button";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/8bit/tooltip";

export default function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const ls = localStorage.getItem("theme");
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const currentDark = ls ? ls === "dark" : prefersDark;
      setIsDark(currentDark);
    } catch {}
  }, []);

  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    try {
      const root = document.documentElement;
      if (next) {
        root.classList.add("dark");
        localStorage.setItem("theme", "dark");
      } else {
        root.classList.remove("dark");
        localStorage.setItem("theme", "light");
      }
      window.dispatchEvent(new CustomEvent("themechange", { detail: { dark: next } }));
    } catch {}
  };

  // Avoid hydration mismatch; render a placeholder until mounted
  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" aria-label="Toggle theme" className="opacity-0 pointer-events-none">
        <Sun className="w-5 h-5" />
      </Button>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          aria-label="Toggle theme"
          aria-pressed={isDark}
          className="group transition-transform hover:scale-105"
        >
          {isDark ? (
            <Moon className="w-5 h-5 text-primary transition-colors duration-300 group-hover:text-ring" />
          ) : (
            <Sun className="w-5 h-5 text-primary transition-colors duration-300 group-hover:text-ring" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>{isDark ? "Switch to light" : "Switch to dark"}</TooltipContent>
    </Tooltip>
  );
}
