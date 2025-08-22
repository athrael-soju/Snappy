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
      <DialogContent className="w-[35vw] !max-w-[95vw] sm:!max-w-[95vw] max-h-[95vh] !p-0 overflow-hidden">
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Image"}</DialogTitle>
          <DialogDescription>Full size image view</DialogDescription>
        </DialogHeader>

        <div className="relative flex items-start justify-center bg-background/95 backdrop-blur-sm max-h-[95vh] overflow-auto">
          <img
            src={src}
            alt={alt || "Full image"}
            className="w-full h-auto object-contain rounded-md shadow-2xl"
          />
        </div>

        {alt && (
          <div className="px-6 pb-6">
            <p className="text-center text-sm text-muted-foreground line-clamp-3">
              {alt}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
