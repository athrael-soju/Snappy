"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type MortyMetaCardBullet = {
  icon: LucideIcon;
  text: string;
};

type MortyMetaCardProps = {
  label: string;
  title: string;
  bullets: MortyMetaCardBullet[];
  image: {
    src: string;
    alt: string;
    width?: number;
    height?: number;
  };
  className?: string;
  glowClassName?: string;
};

const DEFAULT_IMAGE_SIZE = 260;

export function MortyMetaCard({
  label,
  title,
  bullets,
  image,
  className,
  glowClassName,
}: MortyMetaCardProps) {
  const { src, alt, width = DEFAULT_IMAGE_SIZE, height = DEFAULT_IMAGE_SIZE } = image;

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/25 bg-white/10 p-5 text-left text-white shadow-lg backdrop-blur-md sm:p-6",
        className,
      )}
    >
      <div className="grid gap-6 items-center sm:grid-cols-[minmax(0,1fr)_minmax(0,280px)] sm:gap-8">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1.5 text-body-xs font-semibold uppercase tracking-wide text-white/85 backdrop-blur-sm">
            {label}
          </div>
          <h3 className="text-body-lg font-semibold leading-snug text-white sm:text-digital-h3">
            {title}
          </h3>
          <ul className="space-y-2.5 text-body-xs text-white/85 sm:text-body-sm">
            {bullets.map((bullet, index) => (
              <li key={index} className="flex items-start gap-2.5">
                <bullet.icon className="size-icon-sm mt-0.5 shrink-0 text-chart-2" />
                <span className="leading-relaxed">{bullet.text}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative mx-auto flex w-full max-w-[280px] items-center justify-center">
          <motion.div
            className={cn(
              "absolute inset-0 scale-125 rounded-full bg-gradient-to-br from-white/25 via-[#6fb5ff4d] to-[#c084fc4d] blur-3xl",
              glowClassName,
            )}
            animate={{ opacity: [0.3, 0.6, 0.3], scale: [1.05, 1.2, 1.05] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="relative"
            animate={{ y: [0, -10, 0], rotate: [-2, 2, -2] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          >
            <Image
              src={src}
              alt={alt}
              width={width}
              height={height}
              className="relative z-10 drop-shadow-2xl"
              priority
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
