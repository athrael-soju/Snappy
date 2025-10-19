"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type RouteHeroProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  align?: "center" | "left";
  actions?: ReactNode;
  meta?: ReactNode;
  className?: string;
};

/**
 * Shared route hero that mirrors the Vultr marketing header treatment.
 * Renders a blue gradient band with optional actions and metadata and adds
 * the angled white wedge that transitions into the page surface.
 */
export function RouteHero({
  eyebrow,
  title,
  description,
  align = "center",
  actions,
  meta,
  className,
}: RouteHeroProps) {
  const alignment =
    align === "center"
      ? "items-center text-center"
      : "items-start text-left lg:items-start lg:text-left";

  const containerWidth =
    align === "center" ? "mx-auto max-w-4xl" : "max-w-5xl lg:ml-0";

  return (
    <section
      className={cn(
        "relative isolate overflow-hidden bg-gradient-to-br from-[#06175a] via-[#0d2c96] to-[#1647d1] px-6 pb-20 pt-24 text-white shadow-[0_30px_80px_-40px_rgba(8,23,89,0.65)] sm:px-10 md:pb-24 md:pt-28",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_25%,rgba(82,186,255,0.25),transparent_55%),radial-gradient(circle_at_85%_20%,rgba(0,123,252,0.35),transparent_60%)]" />
      <div className="relative mx-auto flex flex-col gap-6">
        <div className={cn("flex flex-col gap-4", alignment, containerWidth)}>
          {eyebrow ? (
            <span className="text-sm font-medium uppercase tracking-[0.28em] text-white/70">
              {eyebrow}
            </span>
          ) : null}
          <div className="flex flex-col gap-4">
            <h1 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl lg:text-5xl">
              {title}
            </h1>
            {description ? (
              <p className="text-base leading-relaxed text-white/80 sm:text-lg">
                {description}
              </p>
            ) : null}
          </div>
          {actions ? (
            <div
              className={cn(
                "flex flex-wrap items-center gap-3",
                align === "center" ? "justify-center" : "justify-start",
              )}
            >
              {actions}
            </div>
          ) : null}
          {meta ? (
            <div
              className={cn(
                "flex flex-wrap items-center gap-2 text-sm text-white/75",
                align === "center" ? "justify-center" : "justify-start",
              )}
            >
              {meta}
            </div>
          ) : null}
        </div>
      </div>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-0 left-1/2 h-20 w-[180%] -translate-x-1/2 bg-white dark:bg-vultr-midnight"
        style={{ clipPath: "polygon(0 0, 100% 45%, 100% 100%, 0 100%)" }}
      />
    </section>
  );
}

