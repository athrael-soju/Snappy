"use client";

import { useEffect } from "react";
import { X } from "lucide-react";

export type ImageLightboxProps = {
  open: boolean;
  src: string;
  alt?: string;
  onOpenChange: (open: boolean) => void;
};

export default function ImageLightbox({ open, src, alt, onOpenChange }: ImageLightboxProps) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", onKeyDown);

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
      onClick={() => onOpenChange(false)}
      role="dialog"
      aria-modal="true"
    >
      {/* Close button */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onOpenChange(false);
        }}
        className="absolute right-4 top-4 inline-flex items-center justify-center rounded-md bg-white/10 p-2 text-white hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white"
        aria-label="Close"
      >
        <X className="h-5 w-5" />
      </button>

      {/* Image */}
      <div className="max-h-[90vh] max-w-[95vw]" onClick={(e) => e.stopPropagation()}>
        {/* Using img to avoid next/image domain constraints in overlay */}
        <img
          src={src}
          alt={alt || "Full image"}
          className="max-h-[90vh] max-w-[95vw] object-contain rounded-md shadow-2xl"
        />
        {alt && (
          <div className="mt-3 text-center text-sm text-white/90 line-clamp-3">
            {alt}
          </div>
        )}
      </div>
    </div>
  );
}
