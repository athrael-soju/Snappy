"use client";

import Image from "next/image";
import { motion, type Variants } from "framer-motion";

export const MORTY_SIZE = 240;
export const MORTY_CENTER_OFFSET = MORTY_SIZE / 2;
export const MORTY_VERTICAL_OFFSET = -75;
export const MORTY_HORIZONTAL_OFFSET = 40;
const mortyVariants: Variants = {
  hidden: {
    opacity: 0,
    x: "100vw",
    y: MORTY_VERTICAL_OFFSET - 25,
    rotate: 45,
    scale: 0.5,
  },
  visible: {
    opacity: 1,
    x: MORTY_HORIZONTAL_OFFSET,
    y: MORTY_VERTICAL_OFFSET,
    rotate: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 80,
      damping: 20,
      delay: 0.6,
      duration: 1.2,
    },
  },
};

type MortyHeroProps = {
  mortyLeft: number;
  mortyCenterLeft: number;
};

export function MortyHero({ mortyLeft, mortyCenterLeft }: MortyHeroProps) {
  return (
    <>
      {/* Comet dust trail - follows Morty during entrance - Bigger and centered */}
      <motion.div
        className="absolute top-1/2 z-15 hidden -translate-y-1/2 lg:block"
        style={{
          left: mortyCenterLeft,
          y: MORTY_VERTICAL_OFFSET,
        }}
        initial={{ opacity: 0 }}
        animate={{
          opacity: [0, 1, 1, 0],
          x: ["100vw", "50vw", "10vw", 0],
        }}
        transition={{
          duration: 1.8,
          delay: 0.6,
          ease: "easeOut",
        }}
      >
        {/* Main comet trail - properly centered on Morty */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          initial={{ x: "120vw", scaleX: 0, opacity: 0 }}
          animate={{
            x: 60,
            scaleX: [0, 6, 3, 0],
            opacity: [0, 0.9, 0.5, 0],
          }}
          transition={{ duration: 2, delay: 0.6, ease: "easeOut" }}
        >
          <div className="h-8 w-[600px] origin-right bg-gradient-to-l from-transparent via-blue-400/70 to-purple-500/90 blur-md" />
        </motion.div>

        {/* Secondary trail - slightly above center */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          style={{ y: -5 }}
          initial={{ x: "115vw", scaleX: 0, opacity: 0 }}
          animate={{
            x: 80,
            scaleX: [0, 5, 2.5, 0],
            opacity: [0, 0.7, 0.4, 0],
          }}
          transition={{ duration: 1.8, delay: 0.7, ease: "easeOut" }}
        >
          <div className="h-6 w-[480px] origin-right bg-gradient-to-l from-transparent via-cyan-400/60 to-pink-500/80 blur-lg" />
        </motion.div>

        {/* Third trail layer - slightly below center */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          style={{ y: 5 }}
          initial={{ x: "110vw", scaleX: 0, opacity: 0 }}
          animate={{
            x: 100,
            scaleX: [0, 4, 2, 0],
            opacity: [0, 0.6, 0.3, 0],
          }}
          transition={{ duration: 1.6, delay: 0.8, ease: "easeOut" }}
        >
          <div className="h-5 w-[420px] origin-right bg-gradient-to-l from-transparent via-purple-400/50 to-blue-400/70 blur-xl" />
        </motion.div>

        {/* Larger comet dust particles - properly centered around Morty */}
        {Array.from({ length: 16 }).map((_, i) => {
          // Use fixed positions to avoid hydration mismatches
          const verticalOffsets = [0, -15, 20, -10, 25, -20, 15, -5, 30, -25, 10, -30, 5, -12, 18, -8];
          return (
            <motion.div
              key={i}
              className="absolute top-1/2 -translate-y-1/2"
              style={{
                left: i * 60 + MORTY_CENTER_OFFSET,
                y: verticalOffsets[i],
              }}
              initial={{
                opacity: 0,
                scale: 0,
                x: 0,
              }}
              animate={{
                opacity: [0, 0.9, 0.5, 0],
                scale: [0, 1.8, 1.2, 0],
                x: [-30, -60, -90],
              }}
              transition={{
                duration: 1,
                delay: i * 0.04 + 0.8,
                ease: "easeOut",
              }}
            >
              <div
                className="h-4 w-4 rounded-full"
                style={{
                  background: `radial-gradient(circle, 
                      ${i % 4 === 0 ? "#60a5fa" : ""}
                      ${i % 4 === 1 ? "#a78bfa" : ""}
                      ${i % 4 === 2 ? "#f472b6" : ""}
                      ${i % 4 === 3 ? "#22d3ee" : ""}
                      , transparent 70%)`,
                  boxShadow: `0 0 16px ${i % 4 === 0
                    ? "#60a5fa"
                    : i % 4 === 1
                      ? "#a78bfa"
                      : i % 4 === 2
                        ? "#f472b6"
                        : "#22d3ee"
                    }`,
                }}
              />
            </motion.div>
          );
        })}

        {/* Bigger trailing energy streaks - properly centered */}
        {Array.from({ length: 8 }).map((_, i) => {
          // Use fixed positions to avoid hydration mismatches
          const verticalOffsets = [0, -12, 18, -8, 15, -18, 10, -15];
          return (
            <motion.div
              key={`streak-${i}`}
              className="absolute top-1/2 -translate-y-1/2"
              style={{
                left: i * 80 + MORTY_CENTER_OFFSET,
                y: verticalOffsets[i],
                width: 120 - i * 8,
                height: 6,
              }}
              initial={{
                opacity: 0,
                scaleX: 0,
              }}
              animate={{
                opacity: [0, 0.8, 0.4, 0],
                scaleX: [0, 1.5, 0.8, 0],
                x: [-40, -70, -100],
              }}
              transition={{
                duration: 1.2,
                delay: i * 0.06 + 0.7,
                ease: "easeOut",
              }}
            >
              <div
                className="h-full w-full rounded-full blur-md"
                style={{
                  background: `linear-gradient(90deg, 
                      transparent, 
                      ${i % 3 === 0 ? "#60a5facc" : ""}
                      ${i % 3 === 1 ? "#a78bfacc" : ""}
                      ${i % 3 === 2 ? "#f472b6cc" : ""}
                    )`,
                }}
              />
            </motion.div>
          );
        })}
      </motion.div>

      {/* Comet dust trail - follows Morty during entrance */}
      <motion.div
        className="absolute top-1/2 z-15 hidden -translate-y-1/2 lg:block"
        style={{
          left: mortyCenterLeft,
          y: MORTY_VERTICAL_OFFSET,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 1, 1, 0] }}
        transition={{ duration: 2, delay: 0.6, ease: "easeOut" }}
      >
        {/* Main comet trail */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          initial={{ x: "100vw", scaleX: 0 }}
          animate={{ x: 0, scaleX: [0, 3, 1, 0] }}
          transition={{ duration: 1.8, delay: 0.6, ease: "easeOut" }}
        >
          <div className="h-2 w-96 origin-right bg-gradient-to-l from-transparent via-blue-300/60 to-purple-400/80 blur-sm" />
        </motion.div>

        {/* Secondary trail particles */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          style={{ y: -4 }}
          initial={{ x: "100vw", scaleX: 0 }}
          animate={{ x: 20, scaleX: [0, 2.5, 0.8, 0] }}
          transition={{ duration: 1.6, delay: 0.7, ease: "easeOut" }}
        >
          <div className="h-1 w-72 origin-right bg-gradient-to-l from-transparent via-cyan-300/40 to-pink-400/60 blur-md" />
        </motion.div>

        {/* Sparkle dust particles */}
        {Array.from({ length: 8 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute top-1/2 -translate-y-1/2"
            initial={{
              x: `${80 + i * 15}vw`,
              y: (i % 2 === 0 ? -1 : 1) * (10 + i * 3),
              opacity: 0,
              scale: 0,
            }}
            animate={{
              x: i * 25,
              y: (i % 2 === 0 ? -1 : 1) * (5 + i * 2),
              opacity: [0, 1, 1, 0],
              scale: [0, 1, 0.5, 0],
            }}
            transition={{
              duration: 1.2 + i * 0.1,
              delay: 0.8 + i * 0.05,
              ease: "easeOut",
            }}
          >
            <div
              className={`h-1 w-1 rounded-full ${i % 4 === 0 ? "bg-blue-300" : i % 4 === 1 ? "bg-purple-300" : i % 4 === 2 ? "bg-pink-300" : "bg-cyan-300"} shadow-lg shadow-current/50 blur-[0.5px]`}
            />
          </motion.div>
        ))}

        {/* Wispy smoke trails */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          style={{ y: 3 }}
          initial={{ x: "100vw", scaleX: 0, opacity: 0 }}
          animate={{
            x: 40,
            scaleX: [0, 4, 2, 0],
            opacity: [0, 0.6, 0.3, 0],
          }}
          transition={{ duration: 2.2, delay: 0.5, ease: "easeOut" }}
        >
          <div className="h-3 w-80 origin-right bg-gradient-to-l from-transparent via-white/20 to-blue-200/40 blur-lg" />
        </motion.div>
      </motion.div>

      {/* Morty Mascot - Overlay positioned absolutely */}
      <motion.div
        className="absolute top-1/2 z-20 hidden -translate-y-1/2 lg:block"
        style={{ left: mortyLeft }}
        variants={mortyVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div
          className="relative"
          animate={{
            y: [0, -8, 0],
            rotate: [-1, 1, -1],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          {/* Powerful energy glow layers */}
          {/* Outer energy ring - pulsing */}
          <motion.div
            className="absolute inset-0 -z-30 scale-150"
            animate={{
              opacity: [0.3, 0.7, 0.3],
              scale: [1.4, 1.6, 1.4],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="h-full w-full rounded-full bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 blur-2xl" />
          </motion.div>

          {/* Middle energy layer - rotating */}
          <motion.div
            className="absolute inset-0 -z-20 scale-125"
            animate={{
              rotate: [0, 360],
              opacity: [0.4, 0.8, 0.4],
            }}
            transition={{
              rotate: { duration: 8, repeat: Infinity, ease: "linear" },
              opacity: { duration: 3, repeat: Infinity, ease: "easeInOut" },
            }}
          >
            <div className="h-full w-full rounded-full bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 blur-xl" />
          </motion.div>

          {/* Inner intense glow */}
          <motion.div
            className="absolute inset-0 -z-10 scale-110"
            animate={{
              opacity: [0.6, 1, 0.6],
              scale: [1.05, 1.15, 1.05],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="h-full w-full rounded-full bg-gradient-to-r from-white via-blue-300 to-purple-400 blur-lg" />
          </motion.div>

          {/* Core energy spark */}
          <motion.div
            className="absolute inset-0 -z-5"
            animate={{
              opacity: [0.8, 1, 0.8],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="h-full w-full rounded-full bg-white/30 blur-md" />
          </motion.div>

          <Image
            src="/vultr/morty_notext.png"
            alt="Morty - Vultr Vision Mascot"
            width={MORTY_SIZE}
            height={MORTY_SIZE}
            className="relative z-10 drop-shadow-2xl brightness-110 contrast-110"
            priority
          />

          {/* Energy particles effect */}
          <motion.div
            className="absolute inset-0 z-5"
            animate={{
              rotate: [0, 360],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "linear",
            }}
          >
            {/* Small energy dots */}
            <div className="absolute -top-2 left-1/2 h-1 w-1 rounded-full bg-blue-300 shadow-lg shadow-blue-400/50" />
            <div className="absolute right-2 top-1/3 h-1 w-1 rounded-full bg-purple-300 shadow-lg shadow-purple-400/50" />
            <div className="absolute bottom-4 right-1/3 h-1 w-1 rounded-full bg-pink-300 shadow-lg shadow-pink-400/50" />
            <div className="absolute bottom-2 left-1/4 h-1 w-1 rounded-full bg-cyan-300 shadow-lg shadow-cyan-400/50" />
          </motion.div>
        </motion.div>
      </motion.div>
    </>
  );
}

