"use client";

import { ReactNode } from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export type ImageLightboxProps = {
  open: boolean;
  src: string;
  alt?: string;
  onOpenChange: (open: boolean) => void;
  children?: ReactNode;
};

export default function ImageLightbox({ open, src, alt, onOpenChange, children }: ImageLightboxProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-fit sm:!max-w-fit !max-h-[98vh] p-0 overflow-hidden flex flex-col w-auto">
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Image"}</DialogTitle>
          <DialogDescription>Full size image view</DialogDescription>
        </DialogHeader>

        <div className="relative flex items-center justify-center bg-background p-0">
          {children ? (
            <div className="max-h-[93vh] max-w-[95vw] h-full w-full overflow-hidden">
              {children}
            </div>
          ) : src ? (
            <img
              src={src}
              alt={alt || "Full image"}
              className="max-h-[93vh] max-w-[95vw] h-auto w-auto object-contain"
            />
          ) : null}
        </div>

        {alt && (
          <div className="border-t px-4 py-3">
            <p className="text-center text-body-xs text-muted-foreground line-clamp-2">
              {alt}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
