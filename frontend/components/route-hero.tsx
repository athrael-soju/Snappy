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
  variant?: "default" | "compact";
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
  variant = "default",
}: RouteHeroProps) {
  if (variant === "compact") {
    const leftAlignment =
      align === "center"
        ? "items-center text-center md:items-start md:text-left"
        : "items-start text-left";

    return (
      <section
        className={cn(
          "relative isolate overflow-hidden bg-gradient-to-br from-[#06175a] via-[#0d2c96] to-[#1647d1] px-4 py-10 text-white shadow-[0_26px_64px_-42px_rgba(8,23,89,0.7)] sm:px-6 lg:px-8",
          className,
        )}
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_25%,rgba(82,186,255,0.25),transparent_55%),radial-gradient(circle_at_85%_20%,rgba(0,123,252,0.35),transparent_60%)]" />
        <div className="relative mx-auto flex w-full max-w-5xl flex-col gap-6 md:grid md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] md:items-start md:gap-8">
          <div
            className={cn(
              "flex flex-col gap-2 md:max-w-3xl",
              leftAlignment,
              align === "center" ? "mx-auto md:mx-0" : "",
            )}
          >
            {eyebrow ? <span className="eyebrow text-white/70">{eyebrow}</span> : null}
            <div className="flex flex-col gap-2">
              <h1 className="text-digital-h3 text-balance font-semibold text-white md:text-digital-h2">
                {title}
              </h1>
              {description ? (
                <p className="text-body-sm text-white/80 md:text-body">
                  {description}
                </p>
              ) : null}
            </div>
          </div>

          {(actions || meta) ? (
            <div className="flex w-full flex-col gap-3 md:max-w-sm md:justify-self-end">
              {actions ? (
                <div
                  className={cn(
                    "flex flex-wrap items-center gap-2 text-body-sm md:gap-3",
                    align === "center" ? "justify-center md:justify-end" : "justify-start md:justify-end",
                  )}
                >
                  {actions}
                </div>
              ) : null}

              {meta ? (
                <div
                  className={cn(
                    "flex flex-wrap items-center gap-2 rounded-xl px-3 py-2 text-body-xs text-white/75 backdrop-blur-sm md:justify-end",
                    align === "center" ? "justify-center md:justify-end" : "justify-start md:justify-end",
                  )}
                >
                  {meta}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute bottom-0 left-1/2 h-10 w-[160%] -translate-x-1/2 bg-white dark:bg-vultr-midnight"
          style={{ clipPath: "polygon(0 0, 100% 45%, 100% 100%, 0 100%)" }}
        />
      </section>
    );
  }

  const alignment =
    align === "center"
      ? "items-center text-center"
      : "items-start text-left lg:items-start lg:text-left";

  const containerWidth =
    align === "center" ? "mx-auto max-w-4xl" : "max-w-5xl lg:ml-0";

  const variantPadding =
    variant === "default"
      ? "pb-12 pt-16 md:pb-16 md:pt-20"
      : "pb-20 pt-24 md:pb-24 md:pt-28";

  const wedgeHeight = variant === "default" ? "h-16" : "h-20";

  return (
    <section
      className={cn(
        "relative isolate overflow-hidden bg-gradient-to-br from-[#06175a] via-[#0d2c96] to-[#1647d1] px-6 text-white shadow-[0_30px_80px_-40px_rgba(8,23,89,0.65)] sm:px-10",
        variantPadding,
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_25%,rgba(82,186,255,0.25),transparent_55%),radial-gradient(circle_at_85%_20%,rgba(0,123,252,0.35),transparent_60%)]" />
      <div className="relative mx-auto flex flex-col gap-6">
        <div className={cn("flex flex-col gap-4", alignment, containerWidth)}>
          {eyebrow ? (
            <span className="eyebrow text-white/70">{eyebrow}</span>
          ) : null}
          <div className="flex flex-col gap-4">
            <h1 className="text-digital-h2 text-balance font-semibold text-white">
              {title}
            </h1>
            {description ? (
              <p className="text-body text-white/85">
                {description}
              </p>
            ) : null}
          </div>
          {actions ? (
            <div
              className={cn(
                "flex flex-wrap items-center gap-3 text-body-sm",
                align === "center" ? "justify-center" : "justify-start",
              )}
            >
              {actions}
            </div>
          ) : null}
          {meta ? (
            <div
              className={cn(
                "flex flex-wrap items-center gap-2 text-body-xs text-white/80",
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
        className={cn(
          "pointer-events-none absolute bottom-0 left-1/2 w-[180%] -translate-x-1/2 bg-white dark:bg-vultr-midnight",
          wedgeHeight,
        )}
        style={{ clipPath: "polygon(0 0, 100% 45%, 100% 100%, 0 100%)" }}
      />
    </section>
  );
}

