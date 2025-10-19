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
  className?: string;
  contentWrapperClassName?: string;
  innerClassName?: string;
  children: ReactNode;
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
  className,
  contentWrapperClassName,
  innerClassName,
  children,
}: RoutePageShellProps) {
  return (
    <div
      className={cn(
        "relative flex flex-1 flex-col bg-white pt-16 dark:bg-vultr-midnight",
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
      />
      <div
        className={cn(
          "relative z-10 flex flex-1 flex-col overflow-hidden bg-gradient-to-b from-white via-[#f7f9ff] to-white px-4 py-12 sm:px-6 lg:px-8 dark:from-vultr-midnight dark:via-[#0f1c4d] dark:to-vultr-midnight",
          contentWrapperClassName,
        )}
      >
        <div
          className={cn(
            "mx-auto flex w-full max-w-5xl flex-col space-y-6",
            innerClassName,
          )}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

