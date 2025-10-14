"use client";

import { Suspense, useMemo } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Home, Search as SearchIcon, Upload, MessageSquare, Menu } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { ThemeSwitch } from "@/components/theme-switch";
import { NavUser } from "@/components/nav-user";
import { useAppStore } from "@/stores/app-store";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/search", label: "Search", icon: SearchIcon },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/chat", label: "Chat", icon: MessageSquare },
] as const;

function NavLinks({ orientation = "horizontal" }: { orientation?: "horizontal" | "vertical" }) {
  const pathname = usePathname();
  const { state } = useAppStore();

  const uploadStatus = useMemo(() => {
    const uploading = state.upload.uploading;
    const progress = Math.round(state.upload.uploadProgress ?? 0);
    const hasJob = Boolean(state.upload.jobId);

    if (uploading || (progress > 0 && progress < 100) || hasJob) {
      return { label: `${progress}%`, variant: uploading ? "default" : "secondary" } as const;
    }

    return null;
  }, [
    state.upload.uploading,
    state.upload.uploadProgress,
    state.upload.jobId,
  ]);

  return (
    <nav
      className={cn(
        "flex gap-1",
        orientation === "vertical" && "flex-col gap-2"
      )}
    >
      {links.map((link) => {
        const Icon = link.icon;
        const isActive =
          link.href === "/"
            ? pathname === "/"
            : pathname === link.href || pathname.startsWith(`${link.href}/`);

        const isUpload = link.href === "/upload";

        return (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              "hover:bg-secondary hover:text-secondary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              isActive ? "bg-secondary text-secondary-foreground" : "text-muted-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            <span>{link.label}</span>
            {isUpload && uploadStatus && (
              <Badge
                variant={uploadStatus.variant}
                className="ml-1 h-5 text-xs font-semibold"
              >
                {uploadStatus.label}
              </Badge>
            )}
          </Link>
        );
      })}
    </nav>
  );
}

export function Nav() {
  const { resolvedTheme } = useTheme();
  const logoSrc =
    resolvedTheme === "dark"
      ? "/Snappy/snappy_dark_nobg_resized.png"
      : "/Snappy/snappy_light_nobg_resized.png";

  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-3 px-4">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-md px-2 py-1 text-sm font-semibold text-foreground transition-colors hover:bg-secondary hover:text-secondary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <Image
            src={logoSrc}
            width={28}
            height={28}
            alt="Snappy mascot"
            priority
          />
          <span className="hidden text-base sm:inline">Snappy</span>
        </Link>

        <div className="ml-auto flex items-center gap-2 md:gap-3">
          <div className="hidden md:flex">
            <NavLinks />
          </div>

          <div className="hidden items-center gap-2 md:flex">
            <ThemeSwitch />
            <Suspense fallback={null}>
              <NavUser />
            </Suspense>
          </div>

          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                aria-label="Open navigation menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="flex h-full flex-col gap-6">
              <SheetHeader className="text-left">
                <SheetTitle className="text-base font-semibold">Navigation</SheetTitle>
                <SheetDescription className="text-sm text-muted-foreground">
                  Choose a page or update your settings.
                </SheetDescription>
              </SheetHeader>

              <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <Image
                  src={logoSrc}
                  width={32}
                  height={32}
                  alt="Snappy mascot"
                />
                <span>Snappy</span>
              </Link>
              <NavLinks orientation="vertical" />
              <div className="mt-auto flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Theme</span>
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
    </header>
  );
}
