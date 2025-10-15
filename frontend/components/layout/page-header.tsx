"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <section
      className={cn(
        "page-surface stack-sm gap-[var(--space-3)] p-6 sm:p-7",
        className,
      )}
    >
      <div className="flex flex-col gap-[var(--space-3)]">
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav aria-label="Breadcrumb">
            <ol className="flex flex-wrap items-center gap-1 text-xs font-medium text-muted-foreground">
              {breadcrumbs.map((item, index) => {
                const isLast = index === breadcrumbs.length - 1;
                return (
                  <li key={`${item.label}-${index}`} className="flex items-center gap-1">
                    {item.href && !isLast ? (
                      <Link
                        href={item.href}
                        className="transition-colors hover:text-foreground"
                      >
                        {item.label}
                      </Link>
                    ) : (
                      <span className={cn(isLast ? "text-foreground" : "text-muted-foreground")}>
                        {item.label}
                      </span>
                    )}
                    {!isLast ? <span aria-hidden>›</span> : null}
                  </li>
                );
              })}
            </ol>
          </nav>
        ) : null}

        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            {title}
          </h1>
          {description ? (
            <p className="max-w-prose text-sm text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
      </div>

      {actions ? (
        <div className="flex flex-wrap gap-2 sm:justify-end">{actions}</div>
      ) : null}
    </section>
  );
}
