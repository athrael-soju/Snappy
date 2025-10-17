"use client";
import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";
import { getRandomBrainPlaceholder } from "@/lib/chat/brain-states";
export default function Loading() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [message, setMessage] = useState("Getting things ready");
  useEffect(() => {
    setMounted(true);
  }, []);
  useEffect(() => {
    if (!mounted) return;
    setMessage(`${getRandomBrainPlaceholder()}...`);
    const interval = window.setInterval(() => {
      setMessage(`${getRandomBrainPlaceholder()}...`);
    }, 3000);
    return () => window.clearInterval(interval);
  }, [mounted]);
  const logoSrc = useMemo(
    () =>
      theme === "dark"
        ? "/Snappy/snappy_dark_nobg_resized.png"
        : "/Snappy/snappy_light_nobg_resized.png",
    [theme],
  );
  return (
    <div className="flex h-full w-full items-center justify-center" role="status" aria-live="polite" aria-busy="true">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="relative flex flex-col items-center gap-6"
      >
        {/* Animated gradient spinner */}
        <div className="relative h-24 w-24">
          {/* Pulsing gradient glow - behind everything */}
          <motion.div
            className="absolute -inset-6 rounded-full bg-gradient-to-br from-chart-1/30 via-chart-2/30 to-chart-4/30 blur-2xl"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.4, 0.7, 0.4],
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
          {/* Outer rotating gradient ring */}
          <motion.div
            className="absolute inset-0 rounded-full bg-gradient-to-tr from-chart-1 via-chart-2 to-chart-4 opacity-30 blur-sm"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear", repeatType: "loop" }}
          />
          {/* Main rotating gradient ring */}
          <motion.div
            className="absolute inset-1 rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear", repeatType: "loop" }}
            style={{
              background:
                "conic-gradient(from 0deg, transparent 0%, hsl(var(--chart-1)) 25%, hsl(var(--chart-2)) 50%, hsl(var(--chart-4)) 75%, transparent 100%)",
              WebkitMask:
                "radial-gradient(farthest-side, transparent calc(100% - 6px), black calc(100% - 4px))",
              mask: "radial-gradient(farthest-side, transparent calc(100% - 6px), black calc(100% - 4px))",
            }}
          />
          {/* Center icon - animated */}
          <div className="absolute inset-0 flex items-center justify-center">
            {mounted && (
              <motion.div
                className="relative flex h-16 w-16 items-center justify-center sm:h-20 sm:w-20"
                animate={{ rotate: 360 }}
                transition={{ duration: 6, repeat: Infinity, ease: "linear", repeatType: "loop" }}
              >
                <Image
                  src={logoSrc}
                  alt="Snappy logo"
                  fill
                  sizes="80px"
                  className="object-contain drop-shadow-lg"
                  priority
                />
              </motion.div>
            )}
          </div>
        </div>
        {/* Loading text */}
        <motion.p
          className="text-body-sm leading-relaxed text-foreground/90 sm:text-body"
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", repeatType: "loop" }}
        >
          {message}
        </motion.p>
      </motion.div>
    </div>
  );
}
