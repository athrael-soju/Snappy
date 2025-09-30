"use client";

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
};

export default function ImageLightbox({ open, src, alt, onOpenChange }: ImageLightboxProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-fit max-h-[95vh] !p-0 overflow-hidden flex flex-col">
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Image"}</DialogTitle>
          <DialogDescription>Full size image view</DialogDescription>
        </DialogHeader>

        <div className="relative flex items-center justify-center bg-background">
          <img
            src={src}
            alt={alt || "Full image"}
            className="max-w-[92vw] max-h-[88vh] w-auto h-auto object-contain"
          />
        </div>

        {alt && (
          <div className="px-4 py-3 bg-background border-t">
            <p className="text-center text-xs text-muted-foreground line-clamp-1">
              {alt}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
