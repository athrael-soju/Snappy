"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { BackgroundGradientAnimation } from "@/components/ui/shadcn-io/background-gradient-animation";

/**
 * Theme-aware gradient background animation
 * Dynamically adjusts colors based on light/dark mode
 */
export function AnimatedBackground({ children }: { children?: React.ReactNode }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Light mode colors - vibrant and bright
  const lightModeColors = {
    gradientBackgroundStart: "rgb(250, 245, 235)", // Warm linen
    gradientBackgroundEnd: "rgb(255, 244, 230)", // Soft peach cream
    firstColor: "79, 70, 229", // Indigo
    secondColor: "147, 51, 234", // Purple
    thirdColor: "14, 165, 233", // Sky blue
    fourthColor: "236, 72, 153", // Pink
    fifthColor: "251, 146, 60", // Orange
    pointerColor: "99, 102, 241", // Indigo lighter
  };

  // Dark mode colors - deep and mysterious (matching design system)
  const darkModeColors = {
    gradientBackgroundStart: "rgb(17, 18, 29)", // Matches --surface-0
    gradientBackgroundEnd: "rgb(25, 28, 42)", // Slightly lighter
    firstColor: "124, 58, 237", // Purple
    secondColor: "59, 130, 246", // Blue
    thirdColor: "168, 85, 247", // Purple lighter
    fourthColor: "14, 165, 233", // Sky
    fifthColor: "236, 72, 153", // Pink
    pointerColor: "139, 92, 246", // Violet
  };

  // Default to light mode during SSR to avoid hydration mismatch
  const colors = mounted && resolvedTheme === "dark" ? darkModeColors : lightModeColors;

  // Don't render until mounted to avoid hydration issues
  if (!mounted) {
    return <div className="fixed inset-0 bg-background">{children}</div>;
  }

  return (
    <BackgroundGradientAnimation
      key={resolvedTheme} // Force re-render on theme change
      {...colors}
      size="80%"
      blendingValue="hard-light"
      interactive={true}
      containerClassName="fixed inset-0"
    >
      {children}
    </BackgroundGradientAnimation>
  );
}
