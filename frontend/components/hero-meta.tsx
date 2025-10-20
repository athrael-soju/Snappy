"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { AppButton, type AppButtonProps } from "@/components/app-button";
import { cn } from "@/lib/utils";

type HeroMetaTone = "default" | "success" | "warning" | "danger" | "info";

const toneStyles: Record<HeroMetaTone, string> = {
  default: "border border-white/25 bg-white/10 text-white/85",
  success: "border border-vultr-light-blue/50 bg-vultr-light-blue/20 text-white",
  warning: "border border-amber-300/60 bg-amber-400/20 text-amber-100",
  danger: "border border-rose-400/60 bg-rose-500/20 text-rose-100",
  info: "border border-vultr-blue/45 bg-vultr-blue/20 text-white",
};

const basePillClasses =
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-body-xs font-medium leading-none backdrop-blur-sm";

const iconWrapper = "size-icon-2xs shrink-0";

const isLucideIcon = (icon: LucideIcon | ReactNode | undefined): icon is LucideIcon => {
  if (!icon) return false;

  if (typeof icon === "function") return true;

  if (typeof icon === "object" && icon !== null) {
    const candidate = icon as unknown as Record<string, unknown>;
    const forwardRefSymbol = Symbol.for("react.forward_ref");

    if ("$$typeof" in candidate && candidate["$$typeof"] === forwardRefSymbol) {
      return true;
    }

    if ("render" in candidate && typeof candidate["render"] === "function") {
      return true;
    }
  }

  return false;
};

type HeroMetaPillProps = {
  icon?: LucideIcon | ReactNode;
  tone?: HeroMetaTone;
  className?: string;
  children: ReactNode;
};

export function HeroMetaPill({
  icon,
  tone = "default",
  className,
  children,
}: HeroMetaPillProps) {
  const IconComponent = isLucideIcon(icon) ? icon : null;

  return (
    <span className={cn(basePillClasses, toneStyles[tone], className)}>
      {IconComponent ? (
        <IconComponent className={iconWrapper} aria-hidden="true" />
      ) : icon && !isLucideIcon(icon) ? (
        <span className={cn(iconWrapper, "text-current")} aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <span className="whitespace-nowrap text-current">{children}</span>
    </span>
  );
}

type HeroMetaGroupProps = {
  children: ReactNode;
  className?: string;
};

export function HeroMetaGroup({ children, className }: HeroMetaGroupProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-2 text-body-xs text-white/85",
        className,
      )}
    >
      {children}
    </div>
  );
}

type HeroMetaActionProps = Omit<AppButtonProps, "size" | "variant" | "pill"> & {
  children: ReactNode;
};

export function HeroMetaAction({
  className,
  children,
  ...props
}: HeroMetaActionProps) {
  return (
    <AppButton
      size="xs"
      variant="ghost"
      pill
      {...props}
      className={cn(
        "!border !border-white/30 !bg-white/10 !text-white/90 !backdrop-blur-sm !hover:border-white/45 !hover:bg-white/20 !hover:text-white [&>svg]:size-icon-2xs",
        className,
      )}
    >
      {children}
    </AppButton>
  );
}
