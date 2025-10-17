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
      <DialogContent className="!max-w-fit sm:!max-w-fit !max-h-[98vh] p-0 overflow-hidden flex flex-col w-auto">
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Image"}</DialogTitle>
          <DialogDescription>Full size image view</DialogDescription>
        </DialogHeader>

        <div className="relative flex items-center justify-center bg-background p-0">
          {src ? (
            <img
              src={src}
              alt={alt || "Full image"}
              className="max-h-[93vh] max-w-[95vw] h-auto w-auto object-contain"
            />
          ) : null}
        </div>

        {alt && (
          <div className="px-4 py-3 border-t">
            <p className="text-center text-xs text-muted-foreground line-clamp-2">
              {alt}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
