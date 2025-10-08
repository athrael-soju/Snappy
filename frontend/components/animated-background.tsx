"use client";

import { motion, useScroll, useSpring, useTransform } from "framer-motion";
import { useTheme } from "next-themes";
import { useEffect, useMemo, useState } from "react";
import { BackgroundGradientAnimation } from "@/components/ui/shadcn-io/background-gradient-animation";

/**
 * Theme-aware gradient background animation with parallax orb
 * Dynamically adjusts colors based on light/dark mode
 */
export function AnimatedBackground({ children }: { children?: React.ReactNode }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { scrollYProgress } = useScroll();
  const parallaxOffset = useTransform(scrollYProgress, [0, 1], [-120, 120]);
  const parallaxY = useSpring(parallaxOffset, { stiffness: 120, damping: 26, mass: 0.8 });

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

  const orbGradient = useMemo(
    () =>
      mounted && resolvedTheme === "dark"
        ? "radial-gradient(circle at 35% 35%, rgba(147, 51, 234, 0.32) 0%, rgba(14, 165, 233, 0.24) 45%, rgba(15, 118, 110, 0.18) 70%, transparent 85%)"
        : "radial-gradient(circle at 40% 35%, rgba(99, 102, 241, 0.28) 0%, rgba(14, 165, 233, 0.2) 48%, rgba(236, 72, 153, 0.16) 72%, transparent 90%)",
    [mounted, resolvedTheme]
  );

  // Don't render until mounted to avoid hydration issues
  if (!mounted) {
    return <div className="fixed inset-0 bg-background">{children}</div>;
  }

  return (
    <BackgroundGradientAnimation
      {...colors}
      size="80%"
      blendingValue="hard-light"
      interactive={true}
      containerClassName="fixed inset-0"
    >
      <>
        <motion.div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
        >
          <motion.div
            className="absolute left-[12%] top-[-20%] h-[48vw] max-h-[540px] w-[60vw] max-w-[720px] rounded-full blur-3xl mix-blend-screen"
            style={{
              y: parallaxY,
              background: orbGradient,
              opacity: resolvedTheme === "dark" ? 0.55 : 0.68,
              willChange: "transform",
            }}
            animate={{
              x: ["0%", "3%", "-2%", "0%"],
              rotate: [0, 5, -3, 0],
              scale: [1, 1.03, 0.98, 1],
            }}
            transition={{
              duration: 28,
              repeat: Infinity,
              repeatType: "mirror",
              ease: "easeInOut",
            }}
          />
        </motion.div>
        {children}
      </>
    </BackgroundGradientAnimation>
  );
}
