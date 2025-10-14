"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  Home,
  Search as SearchIcon,
  Upload,
  MessageSquare,
  Settings,
  Wrench,
  Info,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import { ThemeSwitch } from "@/components/theme-switch";
import { NavUser } from "@/components/nav-user";
import { useAppStore } from "@/stores/app-store";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const mainLinks = [
  { href: "/", label: "Home", icon: Home },
  { href: "/search", label: "Search", icon: SearchIcon },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/chat", label: "Chat", icon: MessageSquare },
] as const;

const systemLinks = [
  { href: "/maintenance?section=configuration", label: "Configuration", icon: Settings },
  { href: "/maintenance?section=data", label: "Maintenance", icon: Wrench },
  { href: "/about", label: "About", icon: Info },
] as const;

interface SidebarNavProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function SidebarNav({ collapsed, onToggleCollapse }: SidebarNavProps) {
  const pathname = usePathname();
  const { resolvedTheme } = useTheme();
  const { state } = useAppStore();

  const logoSrc =
    resolvedTheme === "dark"
      ? "/Snappy/snappy_dark_nobg_resized.png"
      : "/Snappy/snappy_light_nobg_resized.png";

  const uploadStatus = useMemo(() => {
    const uploading = state.upload.uploading;
    const progress = Math.round(state.upload.uploadProgress ?? 0);
    const hasJob = Boolean(state.upload.jobId);

    if (uploading || (progress > 0 && progress < 100) || hasJob) {
      return { label: `${progress}%`, variant: uploading ? "default" : "secondary" } as const;
    }

    return null;
  }, [state.upload.uploading, state.upload.uploadProgress, state.upload.jobId]);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-50 flex h-screen flex-col border-r bg-sidebar transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center gap-2 border-b px-4">
        <Link href="/" className="flex items-center gap-3 transition-colors hover:opacity-80">
          <Image src={logoSrc} width={32} height={32} alt="Snappy mascot" priority />
          {!collapsed && <span className="text-lg font-bold">Snappy</span>}
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        <div className="space-y-1">
          {!collapsed && (
            <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/60">
              Main
            </p>
          )}
          {mainLinks.map((link) => {
            const Icon = link.icon;
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname === link.href || pathname.startsWith(`${link.href}/`);
            const isUpload = link.href === "/upload";

            if (collapsed) {
              return (
                <Tooltip key={link.href} delayDuration={0}>
                  <TooltipTrigger asChild>
                    <Link
                      href={link.href}
                      className={cn(
                        "relative flex h-10 items-center justify-center rounded-lg transition-all duration-200",
                        isActive
                          ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                          : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      {isUpload && uploadStatus && (
                        <span className="absolute right-1 top-1 flex h-2 w-2">
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                          <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
                        </span>
                      )}
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>{link.label}</p>
                    {isUpload && uploadStatus && <p className="text-xs">{uploadStatus.label}</p>}
                  </TooltipContent>
                </Tooltip>
              );
            }

            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-lg px-3 transition-all duration-200",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span className="flex-1 truncate text-sm font-medium">{link.label}</span>
                {isUpload && uploadStatus && (
                  <Badge variant={uploadStatus.variant} className="h-5 text-xs font-semibold">
                    {uploadStatus.label}
                  </Badge>
                )}
              </Link>
            );
          })}
        </div>

        <div className="pt-4">
          {!collapsed && (
            <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/60">
              System
            </p>
          )}
          {systemLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || pathname.startsWith(link.href.split("?")[0]);

            if (collapsed) {
              return (
                <Tooltip key={link.href} delayDuration={0}>
                  <TooltipTrigger asChild>
                    <Link
                      href={link.href}
                      className={cn(
                        "flex h-10 items-center justify-center rounded-lg transition-all duration-200",
                        isActive
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>{link.label}</p>
                  </TooltipContent>
                </Tooltip>
              );
            }

            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex h-10 items-center gap-3 rounded-lg px-3 transition-all duration-200",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span className="flex-1 truncate text-sm font-medium">{link.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t p-3">
        {collapsed ? (
          <div className="space-y-2">
            <Tooltip delayDuration={0}>
              <TooltipTrigger asChild>
                <div className="flex justify-center">
                  <ThemeSwitch />
                </div>
              </TooltipTrigger>
              <TooltipContent side="right">Toggle theme</TooltipContent>
            </Tooltip>
            <NavUser collapsed />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-medium text-sidebar-foreground/60">Theme</span>
              <ThemeSwitch />
            </div>
            <NavUser />
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="mt-3 w-full justify-center"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>
    </aside>
  );
}
