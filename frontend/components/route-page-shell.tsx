"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { RouteHero } from "@/components/route-hero";

type RoutePageShellProps = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  align?: "center" | "left";
  actions?: ReactNode;
  meta?: ReactNode;
  metaWrapperClassName?: string;
  className?: string;
  contentWrapperClassName?: string;
  innerClassName?: string;
  children: ReactNode;
  variant?: "default" | "compact";
};

/**
 * Wraps a route with the shared Vultr gradient hero and a light surface body.
 * Keeps spacing consistent with the new header/footer redesign while allowing
 * callers to control the inner layout.
 */
export function RoutePageShell({
  eyebrow,
  title,
  description,
  align = "center",
  actions,
  meta,
  metaWrapperClassName,
  className,
  contentWrapperClassName,
  innerClassName,
  children,
  variant = "default",
}: RoutePageShellProps) {
  const isCompact = variant === "compact";

  return (
    <div
      className={cn(
        "relative flex flex-1 flex-col bg-white dark:bg-vultr-midnight",
        isCompact ? "pt-8 sm:pt-10" : "pt-16",
        className,
      )}
    >
      <RouteHero
        eyebrow={eyebrow}
        title={title}
        description={description}
        align={align}
        actions={actions}
        meta={meta}
        metaWrapperClassName={metaWrapperClassName}
        variant={variant}
      />
      <div
        className={cn(
          "relative z-10 flex flex-1 flex-col overflow-hidden bg-gradient-to-b from-white via-[#f7f9ff] to-white px-4 sm:px-6 lg:px-8 dark:from-vultr-midnight dark:via-[#0f1c4d] dark:to-vultr-midnight",
          isCompact ? "py-6 sm:py-8" : "py-12",
          contentWrapperClassName,
        )}
      >
        <div
          className={cn(
            "mx-auto flex w-full max-w-5xl flex-col",
            isCompact ? "space-y-3 sm:space-y-4" : "space-y-6",
            innerClassName,
          )}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

