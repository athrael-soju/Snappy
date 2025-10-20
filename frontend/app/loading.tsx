"use client";
import { useEffect, useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";

const mortyImages = [
  "/vultr/morty/engi_morty_nobg.png",
  "/vultr/morty/banker_morty_nobg.png",
  "/vultr/morty/dr_morty_nobg.png",
  "/vultr/morty/gamer_morty_nobg.png",
  "/vultr/morty/super_morty_nobg.png",
];

const MORTY_LOADING_MESSAGES = [
  "🚀 Morty is warming up his visual circuits",
  "👀 Scanning documents with eagle eyes",
  "🧠 Processing visual intelligence patterns",
  "📄 Analyzing document structures and layouts",
  "🔍 Enhancing visual search capabilities",
  "📊 Indexing charts and diagrams",
  "🎯 Calibrating multimodal understanding",
  "💫 Connecting visual dots across documents",
  "🎨 Interpreting colors, shapes, and layouts",
  "📐 Mapping spatial relationships in content",
  "🔬 Examining document details microscopically",
  "🎭 Understanding visual context and meaning",
  "🌟 Sparkeling up visual retrieval magic",
  "📈 Analyzing data visualizations",
  "🎪 Preparing the visual intelligence show",
  "🧩 Piecing together visual information",
  "🎯 Fine-tuning document understanding",
  "🚁 Getting a bird's eye view of your content",
  "🎨 Appreciating the artistry in your documents",
  "🔮 Predicting what you're looking for",
];

function getRandomMortyMessage(): string {
  const index = Math.floor(Math.random() * MORTY_LOADING_MESSAGES.length);
  return MORTY_LOADING_MESSAGES[index];
}

export default function Loading() {
  const [mounted, setMounted] = useState(false);
  const [message, setMessage] = useState("Morty is getting ready to help");
  const [mortyImage, setMortyImage] = useState<string>("");
  
  useEffect(() => {
    setMounted(true);
    // Select a random Morty image
    const randomImage = mortyImages[Math.floor(Math.random() * mortyImages.length)];
    setMortyImage(randomImage);
  }, []);
  useEffect(() => {
    if (!mounted) return;
    setMessage(`${getRandomMortyMessage()}...`);
    const interval = window.setInterval(() => {
      setMessage(`${getRandomMortyMessage()}...`);
    }, 3000);
    return () => window.clearInterval(interval);
  }, [mounted]);
  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-white/70 backdrop-blur-sm dark:bg-vultr-midnight/70"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="relative flex flex-col items-center gap-6"
      >
        {/* Animated gradient spinner with Morty-themed colors */}
        <div className="relative h-24 w-24">
          <motion.div
            className="absolute -inset-6 rounded-full bg-gradient-to-br from-vultr-blue/30 via-purple-500/20 to-pink-500/20 blur-2xl"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.4, 0.7, 0.4],
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
          {/* Outer rotating gradient ring */}
          <motion.div
            className="absolute inset-0 rounded-full bg-gradient-to-tr from-vultr-blue via-purple-500/60 to-pink-500/60 opacity-40 blur-sm"
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
                "conic-gradient(from 0deg, transparent 0%, var(--color-vultr-blue) 20%, rgba(168, 85, 247, 0.8) 50%, rgba(236, 72, 153, 0.8) 80%, transparent 100%)",
              WebkitMask:
                "radial-gradient(farthest-side, transparent calc(100% - 6px), black calc(100% - 4px))",
              mask: "radial-gradient(farthest-side, transparent calc(100% - 6px), black calc(100% - 4px))",
            }}
          />
          {/* Center icon - Morty */}
          <div className="absolute inset-0 flex items-center justify-center">
            {mounted && mortyImage && (
              <motion.div
                className="relative flex h-16 w-16 items-center justify-center sm:h-20 sm:w-20 rounded-full bg-white p-2 shadow-lg"
                animate={{
                  rotate: 360,
                  scale: [1, 1.05, 1]
                }}
                transition={{
                  rotate: { duration: 6, repeat: Infinity, ease: "linear", repeatType: "loop" },
                  scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
                }}
              >
                <Image
                  src={mortyImage}
                  alt="Morty - Your Visual Retrieval Buddy"
                  width={64}
                  height={64}
                  className="rounded-full drop-shadow-lg"
                  priority
                />
              </motion.div>
            )}
          </div>
        </div>
        {/* Loading text */}
        <motion.div className="text-center">
          <motion.p
            className="text-body-sm leading-relaxed text-foreground/90 sm:text-body"
            animate={{ opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", repeatType: "loop" }}
          >
            {message}
          </motion.p>
          <motion.p
            className="mt-2 text-body-xs text-foreground/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Morty is preparing your visual intelligence experience
          </motion.p>
        </motion.div>
      </motion.div>
    </div>
  );
}
