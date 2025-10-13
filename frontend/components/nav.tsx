"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Home, Eye, CloudUpload, Brain, Menu } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetTrigger, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useAppStore } from "@/stores/app-store";
import { NavUser } from "@/components/nav-user";
import { ThemeSwitch } from "@/components/theme-switch";

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/search", label: "Search", icon: Eye },
  { href: "/upload", label: "Upload", icon: CloudUpload },
  { href: "/chat", label: "Chat", icon: Brain },
] as const;

const desktopLinkBase =
  "inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors";
const desktopLinkActive = "bg-primary/10 text-primary";
const desktopLinkInactive =
  "text-muted-foreground hover:text-foreground hover:bg-muted/60";

const mobileLinkBase =
  "flex w-full items-center gap-3 rounded-md px-3 py-2 text-base font-medium transition-colors";
const mobileLinkActive = "bg-primary/10 text-primary";
const mobileLinkInactive =
  "text-muted-foreground hover:text-foreground hover:bg-muted/60";

const uploadIndicatorClasses =
  "ml-2 inline-flex items-center justify-center rounded-full bg-primary/90 px-2 py-0.5 text-[10px] font-semibold text-primary-foreground";

interface NavLinkConfig {
  href: string;
  label: string;
  icon: typeof Home;
}

export function Nav() {
  const pathname = usePathname();
  const { state } = useAppStore();
  const [showUploadBadge, setShowUploadBadge] = useState(false);

  const hasUploadProgress =
    state.upload.uploading || (state.upload.uploadProgress > 0 && state.upload.jobId);

  useEffect(() => {
    if (state.upload.uploading || (state.upload.uploadProgress < 100 && state.upload.jobId)) {
      setShowUploadBadge(true);
      return;
    }

    if (!state.upload.uploading && state.upload.uploadProgress >= 100 && !state.upload.jobId) {
      const timer = setTimeout(() => setShowUploadBadge(false), 2400);
      return () => clearTimeout(timer);
    }

    if (!state.upload.jobId && state.upload.uploadProgress === 0) {
      setShowUploadBadge(false);
    }
  }, [state.upload.uploading, state.upload.uploadProgress, state.upload.jobId]);

  const getUploadIndicator = () => {
    if (hasUploadProgress && showUploadBadge) {
      return Math.round(state.upload.uploadProgress);
    }
    return null;
  };

  const renderDesktopLink = (link: NavLinkConfig) => {
    const active =
      link.href === "/"
        ? pathname === "/"
        : pathname === link.href || pathname.startsWith(`${link.href}/`);

    const Icon = link.icon;
    const indicator = link.href === "/upload" ? getUploadIndicator() : null;

    return (
      <Link
        key={link.href}
        href={link.href}
        className={cn(desktopLinkBase, active ? desktopLinkActive : desktopLinkInactive)}
      >
        <Icon className="h-4 w-4" />
        <span>{link.label}</span>
        {indicator !== null && (
          <span className={uploadIndicatorClasses}>{indicator}%</span>
        )}
      </Link>
    );
  };

  const renderMobileLink = (link: NavLinkConfig) => {
    const active =
      link.href === "/"
        ? pathname === "/"
        : pathname === link.href || pathname.startsWith(`${link.href}/`);

    const Icon = link.icon;
    const indicator = link.href === "/upload" ? getUploadIndicator() : null;

    return (
      <Link
        key={link.href}
        href={link.href}
        className={cn(mobileLinkBase, active ? mobileLinkActive : mobileLinkInactive)}
      >
        <Icon className="h-5 w-5" />
        <span className="flex-1">{link.label}</span>
        {indicator !== null && (
          <span className={uploadIndicatorClasses}>{indicator}%</span>
        )}
      </Link>
    );
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur supports-[backdrop-filter]:backdrop-blur">
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="relative h-10 w-10 overflow-hidden rounded-full border border-border/60 bg-card">
            <Image
              src="/Snappy/snappy_light_nobg_resized.png"
              alt="Snappy mascot"
              width={40}
              height={40}
              className="dark:hidden"
              priority
            />
            <Image
              src="/Snappy/snappy_dark_nobg_resized.png"
              alt="Snappy mascot"
              width={40}
              height={40}
              className="hidden dark:block"
              priority
            />
          </span>
          <div className="flex flex-col">
            <span className="text-lg font-semibold leading-tight tracking-tight text-foreground">
              Snappy
            </span>
            <span className="hidden text-xs text-muted-foreground sm:block">
              Visual knowledge in a snap
            </span>
          </div>
        </Link>

        <div className="hidden md:flex items-center gap-1.5">
          {links.map(renderDesktopLink)}
        </div>

        <div className="flex items-center gap-1.5">
          <div className="hidden md:flex items-center gap-1.5">
            <ThemeSwitch />
            <Suspense fallback={null}>
              <NavUser />
            </Suspense>
          </div>

          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Open navigation"
                  className="h-10 w-10 rounded-full border border-border/80 bg-card/80 text-foreground shadow-sm"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="flex h-full flex-col gap-6 bg-background/95 sm:max-w-xs">
                <SheetTitle className="sr-only">Navigation</SheetTitle>
                <div className="flex items-center gap-3 pt-2">
                  <span className="relative h-10 w-10 overflow-hidden rounded-full border border-border/60 bg-card">
                    <Image
                      src="/Snappy/snappy_light_nobg_resized.png"
                      alt="Snappy mascot"
                      width={40}
                      height={40}
                      className="dark:hidden"
                      priority
                    />
                    <Image
                      src="/Snappy/snappy_dark_nobg_resized.png"
                      alt="Snappy mascot"
                      width={40}
                      height={40}
                      className="hidden dark:block"
                      priority
                    />
                  </span>
                  <div className="flex flex-col">
                    <span className="text-base font-semibold text-foreground">
                      Snappy
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Friendly document intelligence
                    </span>
                  </div>
                </div>

                <nav className="flex flex-col gap-1">
                  {links.map(renderMobileLink)}
                </nav>

                <div className="mt-auto flex flex-col gap-4 border-t border-border/60 pt-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-muted-foreground">Theme</span>
                    <ThemeSwitch />
                  </div>
                  <Suspense fallback={null}>
                    <NavUser />
                  </Suspense>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </nav>
    </header>
  );
}
