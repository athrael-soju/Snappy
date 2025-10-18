"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type PageHeaderProps = {
  /**
   * Main heading content. Supports React fragments for gradient spans.
   */
  title: React.ReactNode
  /**
   * Optional supporting copy rendered under the title.
   */
  description?: React.ReactNode
  /**
   * Eyebrow text rendered above the title (e.g., a section label).
   */
  lead?: React.ReactNode
  /**
   * Action area rendered alongside the header (buttons, links, etc.).
   */
  actions?: React.ReactNode
  /**
   * Additional content rendered beneath the description (badges, chips, etc.).
   */
  children?: React.ReactNode
  /**
   * Horizontal alignment for the header stack.
   */
  align?: "left" | "center"
  /**
   * Overall vertical rhythm between header sections.
   */
  spacing?: "sm" | "md" | "lg"
  className?: string
  titleClassName?: string
  descriptionClassName?: string
  leadClassName?: string
  childrenClassName?: string
  actionsClassName?: string
}

const spacingClassMap: Record<NonNullable<PageHeaderProps["spacing"]>, string> = {
  sm: "gap-3",
  md: "gap-4",
  lg: "gap-6",
}

export function PageHeader({
  title,
  description,
  lead,
  actions,
  children,
  align = "center",
  spacing = "md",
  className,
  titleClassName,
  descriptionClassName,
  leadClassName,
  childrenClassName,
  actionsClassName,
}: PageHeaderProps) {
  const alignment = align === "center" ? "items-center text-center" : "items-start text-left"
  const descriptionWidth =
    align === "center" ? "mx-auto max-w-2xl" : "max-w-3xl"
  const actionsAlignment = align === "center" ? "justify-center" : "justify-start"

  return (
    <header
      className={cn(
        "flex flex-col",
        spacingClassMap[spacing],
        alignment,
        className
      )}
    >
      {lead ? (
        <div
          className={cn(
            "text-body-xs font-semibold uppercase tracking-wide text-muted-foreground",
            align === "center" ? "mx-auto" : undefined,
            leadClassName
          )}
        >
          {lead}
        </div>
      ) : null}

      <div
        className={cn(
          "flex flex-col gap-2",
          align === "center" ? "items-center" : "items-start"
        )}
      >
        <h1
          className={cn(
            "text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl",
            titleClassName
          )}
        >
          {title}
        </h1>
        {description ? (
          <div
            className={cn(
              "text-body-xs leading-relaxed text-muted-foreground",
              descriptionWidth,
              descriptionClassName
            )}
          >
            {description}
          </div>
        ) : null}
      </div>

      {actions ? (
        <div
          className={cn(
            "flex flex-wrap items-center gap-3",
            actionsAlignment,
            actionsClassName
          )}
        >
          {actions}
        </div>
      ) : null}

      {children ? (
        <div
          className={cn(
            "flex flex-wrap items-center gap-2",
            actionsAlignment,
            childrenClassName
          )}
        >
          {children}
        </div>
      ) : null}
    </header>
  )
}

