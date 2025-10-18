"use client"

import * as React from "react"
import { Info } from "lucide-react"

import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

type TooltipContentProps = React.ComponentProps<typeof TooltipContent>

type InfoTooltipProps = {
  /**
   * Optional trigger element. Falls back to a circular icon button when omitted.
   */
  trigger?: React.ReactElement
  /**
   * Accessible label applied to the default trigger button.
   */
  triggerAriaLabel?: string
  /**
   * Extra classes merged into the default trigger button.
   */
  triggerClassName?: string
  /**
   * Icon rendered inside the default trigger button.
   */
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>
  /**
   * Extra classes merged into the default icon.
   */
  iconClassName?: string
  /**
   * Optional heading rendered at the top of the tooltip content.
   */
  title?: React.ReactNode
  /**
   * Secondary text rendered beneath the title.
   */
  description?: React.ReactNode
  /**
   * Completely custom tooltip body. When provided, `title` and `description` are ignored.
   */
  content?: React.ReactNode
  /**
   * Extra classes merged into the tooltip content container.
   */
  contentClassName?: string
} & Omit<TooltipContentProps, "children" | "className">

export function InfoTooltip({
  trigger,
  triggerAriaLabel,
  triggerClassName,
  icon: Icon = Info,
  iconClassName,
  title,
  description,
  content,
  contentClassName,
  sideOffset,
  ...contentProps
}: InfoTooltipProps) {
  const resolvedTrigger =
    trigger ??
    (
      <button
        type="button"
        aria-label={
          triggerAriaLabel ??
          (typeof title === "string"
            ? title
            : typeof description === "string"
              ? description
              : "Show details")
        }
        className={cn(
          "inline-flex size-6 items-center justify-center rounded-full border border-transparent text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2",
          triggerClassName
        )}
      >
        <Icon className={cn("size-3", iconClassName)} aria-hidden="true" />
      </button>
    )

  const body = content ?? (
    <div className="space-y-1 text-left">
      {title ? (
        <p className="text-xs font-semibold leading-tight text-background">{title}</p>
      ) : null}
      {description ? (
        <p className="text-[11px] leading-tight text-background/80">{description}</p>
      ) : null}
    </div>
  )

  return (
    <Tooltip>
      <TooltipTrigger asChild>{resolvedTrigger}</TooltipTrigger>
      <TooltipContent
        sideOffset={sideOffset ?? 8}
        {...contentProps}
        className={cn(
          "max-w-lg space-y-1.5 text-left leading-tight",
          contentClassName
        )}
      >
        {body}
      </TooltipContent>
    </Tooltip>
  )
}

export type { InfoTooltipProps }

