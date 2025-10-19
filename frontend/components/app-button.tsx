"use client"

import * as React from "react"

import { cn } from "@/lib/utils"
import { Button as PrimitiveButton } from "@/components/ui/button"

type PrimitiveButtonProps = React.ComponentProps<typeof PrimitiveButton>

type AppButtonVariant =
  | "primary"
  | "outline"
  | "ghost"
  | "cta"
  | "destructive"

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
  "inline-flex items-center justify-center gap-2 font-semibold text-[var(--text-cta)] leading-[var(--leading-cta)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vultr-light-blue focus-visible:ring-offset-2 disabled:opacity-60 disabled:pointer-events-none"

const variantClasses: Record<AppButtonVariant, string> = {
  primary:
    "bg-vultr-blue text-white shadow-[var(--shadow-soft)] hover:brightness-95 active:brightness-90",
  outline:
    "border border-vultr-blue bg-transparent text-vultr-blue hover:bg-vultr-blue hover:text-white",
  ghost:
    "bg-transparent text-vultr-blue hover:bg-vultr-sky-blue/40",
  cta:
    "bg-vultr-blue text-white shadow-[var(--shadow-glow)] hover:brightness-95 active:brightness-90",
  destructive:
    "bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/95",
}

const sizeClasses: Record<AppButtonSize, string> = {
  xs: "h-8 rounded-[calc(var(--radius-card)-0.75rem)] px-3 text-xs [&>svg]:h-3.5 [&>svg]:w-3.5",
  sm: "h-10 px-4 text-sm [&>svg]:h-4 [&>svg]:w-4",
  md: "h-12 px-5 [&>svg]:h-5 [&>svg]:w-5",
  lg: "h-14 px-6 [&>svg]:h-5 [&>svg]:w-5",
  xl: "h-16 px-7 text-lg [&>svg]:h-6 [&>svg]:w-6",
  "icon-sm": "size-8 [&>svg]:h-3.5 [&>svg]:w-3.5",
  icon: "size-10 [&>svg]:h-4 [&>svg]:w-4",
  "icon-lg": "size-12 [&>svg]:h-5 [&>svg]:w-5",
  inline: "h-auto min-h-0 px-0 py-0 text-[inherit] leading-none [&>svg]:h-3.5 [&>svg]:w-3.5",
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
