"use client"

import * as React from "react"

import { cn } from "@/lib/utils"
import { Button as PrimitiveButton } from "@/components/ui/button"

type PrimitiveButtonProps = React.ComponentProps<typeof PrimitiveButton>

type AppButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "destructive"
  | "hero"
  | "glass"
  | "muted"
  | "link"

type AppButtonSize =
  | "xs"
  | "sm"
  | "md"
  | "lg"
  | "xl"
  | "icon-sm"
  | "icon"
  | "icon-lg"
  | "inline"

type AppButtonProps = Omit<PrimitiveButtonProps, "className" | "size" | "variant"> & {
  variant?: AppButtonVariant
  size?: AppButtonSize
  /**
   * Controls the horizontal padding/height preset.
   */
  fullWidth?: boolean
  /**
   * Adds a soft elevation shadow.
   */
  elevated?: boolean
  /**
   * Retains the rounded-full styling. Automatically disabled for inline buttons.
   */
  pill?: boolean
  /**
   * Adjust the horizontal alignment of button content.
   */
  align?: "center" | "start" | "between"
  /**
   * Adds a group class so trailing icons can react to hover via `group-hover/app-button:*` utilities.
   */
  iconShift?: boolean
  /**
   * Indicates the button participates in a segmented group.
   */
  groupPosition?: "start" | "middle" | "end"
}

const baseClasses =
  "inline-flex items-center gap-2 font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-60 disabled:pointer-events-none"

const variantClasses: Record<AppButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-primary/30",
  secondary:
    "bg-secondary text-secondary-foreground hover:bg-secondary/80 focus-visible:ring-secondary/30",
  outline:
    "border border-border/60 bg-background text-foreground hover:border-primary/50 hover:bg-background/90 focus-visible:ring-primary/25",
  ghost:
    "bg-transparent text-muted-foreground hover:bg-muted/40 hover:text-foreground focus-visible:ring-muted/40",
  destructive:
    "bg-destructive text-destructive-foreground hover:bg-destructive/90 focus-visible:ring-destructive/40",
  hero:
    "bg-gradient-to-r from-primary via-chart-4 to-chart-1 text-primary-foreground hover:from-primary/90 hover:via-chart-4/85 hover:to-chart-1/90 focus-visible:ring-primary/40",
  glass:
    "border border-white/15 bg-background/65 text-foreground backdrop-blur-md hover:border-primary/30 focus-visible:ring-primary/25 dark:border-white/5",
  muted:
    "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80 focus-visible:ring-muted/40",
  link:
    "bg-transparent px-0 py-0 text-primary underline-offset-4 hover:underline focus-visible:ring-primary/25",
}

const sizeClasses: Record<AppButtonSize, string> = {
  xs: "h-7 px-2 text-xs [&>svg]:size-icon-3xs",
  sm: "h-9 px-3 text-sm [&>svg]:size-icon-2xs",
  md: "h-10 px-4 text-sm [&>svg]:size-icon-xs",
  lg: "h-12 px-5 text-base [&>svg]:size-icon-sm",
  xl: "h-14 px-6 text-base [&>svg]:size-icon-md",
  "icon-sm": "size-8 [&>svg]:size-icon-2xs",
  icon: "size-10 [&>svg]:size-icon-xs",
  "icon-lg": "size-12 [&>svg]:size-icon-md",
  inline: "h-auto min-h-0 px-0 py-0 text-[inherit] leading-none [&>svg]:size-icon-3xs",
}

const alignClasses: Record<NonNullable<AppButtonProps["align"]>, string> = {
  center: "justify-center",
  start: "justify-start",
  between: "justify-between",
}

const groupShapeClasses: Record<NonNullable<AppButtonProps["groupPosition"]>, string> = {
  start: "rounded-l-full rounded-r-none",
  middle: "rounded-none",
  end: "rounded-r-full rounded-l-none",
}

const groupOverlapClasses: Record<NonNullable<AppButtonProps["groupPosition"]>, string> = {
  start: "",
  middle: "-ml-px",
  end: "-ml-px",
}

export function AppButton({
  variant = "primary",
  size = "md",
  fullWidth,
  elevated,
  pill,
  align = "center",
  iconShift,
  groupPosition,
  ...props
}: AppButtonProps) {
  const isInline = size === "inline"
  const isGrouped = groupPosition !== undefined
  const resolvedPill = isGrouped ? false : pill ?? !isInline
  const resolvedGroupPosition = groupPosition ?? null

  return (
    <PrimitiveButton
      {...props}
      className={cn(
        baseClasses,
        alignClasses[align],
        sizeClasses[size],
        variantClasses[variant],
        resolvedPill ? "rounded-full" : "rounded-md",
        resolvedGroupPosition ? groupShapeClasses[resolvedGroupPosition] : undefined,
        resolvedGroupPosition ? groupOverlapClasses[resolvedGroupPosition] : undefined,
        fullWidth ? "w-full" : "w-fit",
        elevated ? "shadow-lg shadow-primary/20" : "shadow-none",
        iconShift ? "group/app-button" : "",
        props.disabled ? "opacity-60" : ""
      )}
      data-variant={variant}
      data-size={size}
      data-group-position={resolvedGroupPosition ?? undefined}
    />
  )
}

export type { AppButtonProps }
