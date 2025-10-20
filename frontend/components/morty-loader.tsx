"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

const mortyImages = [
  "/vultr/morty/engi_morty_nobg.png",
  "/vultr/morty/banker_morty_nobg.png",
  "/vultr/morty/dr_morty_nobg.png",
  "/vultr/morty/gamer_morty_nobg.png",
  "/vultr/morty/super_morty_nobg.png",
];

type MortyLoaderProps = {
  size?: "sm" | "md" | "lg";
  className?: string;
};

/**
 * A loading spinner that displays a random Morty image with a spinning animation
 */
export function MortyLoader({ size = "md", className }: MortyLoaderProps) {
  const [mortyImage, setMortyImage] = useState<string>("");

  useEffect(() => {
    // Select a random Morty image on mount
    const randomImage = mortyImages[Math.floor(Math.random() * mortyImages.length)];
    setMortyImage(randomImage);
  }, []);

  const sizeClasses = {
    sm: "size-8",
    md: "size-12",
    lg: "size-16",
  };

  if (!mortyImage) {
    // Fallback to a simple spinner while image loads
    return (
      <div
        className={cn(
          "animate-spin rounded-full border-2 border-primary border-t-transparent",
          sizeClasses[size],
          className
        )}
        role="status"
        aria-label="Loading"
      />
    );
  }

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", sizeClasses[size], className)}
      role="status"
      aria-label="Loading"
    >
      <div className="animate-spin">
        <Image
          src={mortyImage}
          alt="Loading..."
          width={size === "sm" ? 32 : size === "md" ? 48 : 64}
          height={size === "sm" ? 32 : size === "md" ? 48 : 64}
          className="rounded-full"
          priority
        />
      </div>
    </div>
  );
}
