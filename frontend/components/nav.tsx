"use client";

import { Suspense, useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Home, Eye, CloudUpload, Brain, Menu } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetTrigger, SheetContent } from "@/components/ui/sheet";
import { useAppStore } from "@/stores/app-store";
import { NavUser } from "@/components/nav-user";

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-pink-500" },
  { href: "/search", label: "Search", icon: Eye, color: "text-sky-500" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-cyan-500" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-purple-500" },
];

export function Nav() {
  const pathname = usePathname();
  const { state } = useAppStore();
  const [showUploadBadge, setShowUploadBadge] = useState(true);

  const hasUploadProgress = state.upload.uploading || (state.upload.uploadProgress > 0 && state.upload.jobId);

  useEffect(() => {
    if (!state.upload.uploading && state.upload.uploadProgress >= 100 && !state.upload.jobId) {
      const timer = setTimeout(() => setShowUploadBadge(false), 2400);
      return () => clearTimeout(timer);
    }

    if (state.upload.uploading || (state.upload.uploadProgress < 100 && state.upload.jobId)) {
      setShowUploadBadge(true);
    } else if (!state.upload.jobId && state.upload.uploadProgress === 0) {
      setShowUploadBadge(false);
    }
  }, [state.upload.uploading, state.upload.uploadProgress, state.upload.jobId]);

  const uploadIndicator = () => {
    if (hasUploadProgress && showUploadBadge) {
      return { count: Math.round(state.upload.uploadProgress), isActive: state.upload.uploading };
    }
    return null;
  };

  const renderLink = (link: typeof links[number]) => {
    const active = link.href === "/" ? pathname === "/" : pathname === link.href || pathname.startsWith(link.href + "/");
    const Icon = link.icon;
    const indicator = link.href === "/upload" ? uploadIndicator() : null;

    return (
      <Link
        key={link.href}
        href={link.href}
        className={cn(
          "relative flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pink-400/50",
          active
            ? "bg-gradient-to-r from-pink-500 via-purple-500 to-sky-500 text-white shadow-[0_12px_24px_-18px_rgba(168,85,247,0.8)]"
            : "text-slate-500 hover:text-slate-900 hover:bg-pink-50/60"
        )}
      >
        <Icon className={cn("h-4 w-4", active ? "text-white" : link.color)} />
        <span>{link.label}</span>
        <AnimatePresence>
          {indicator && (
            <motion.div
              initial={{ opacity: 0, scale: 0.4, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.4, y: -8 }}
              transition={{ duration: 0.25, type: "spring", stiffness: 280, damping: 20 }}
              className={cn(
                "absolute -top-2 -right-2 flex h-[20px] min-w-[20px] items-center justify-center rounded-full border border-white/60 text-[10px] font-bold backdrop-blur",
                indicator.isActive ? "bg-cyan-500 text-white shadow" : "bg-slate-600 text-white/90"
              )}
            >
              {indicator.count}%
            </motion.div>
          )}
        </AnimatePresence>
      </Link>
    );
  };

  return (
    <header className="sticky top-0 z-50 border-b-2 border-pink-300/60 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70">
      <nav className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-3 sm:px-6">
        <div className="flex flex-1 items-center justify-start min-w-0">
          <Link
            href="/"
            className="group flex items-center gap-2 sm:gap-3 rounded-full px-2 py-1 transition hover:bg-pink-50/70"
          >
            <Image
              src="/favicon.png"
              alt="App icon"
              width={40}
              height={40}
              className="h-9 w-9 sm:h-10 sm:w-10 drop-shadow-sm"
              priority
            />
            <span className="hidden md:inline bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent text-sm sm:text-base font-semibold tracking-tight">
              FastAPI / Next.js / ColPali Template
            </span>
          </Link>
        </div>

        <div className="hidden md:flex flex-none items-center justify-center">
          <div className="rounded-full bg-gradient-to-r from-pink-400 via-purple-400 to-cyan-400 p-[2px] shadow-[0_16px_32px_-20px_rgba(168,85,247,0.7)]">
            <div className="flex items-center gap-1 rounded-full bg-white/95 px-2 py-1">
              {links.map(renderLink)}
            </div>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-end gap-2">
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Open navigation" className="h-10 w-10 rounded-full border border-pink-200/70 bg-white/90 shadow-sm">
                  <Menu className="h-5 w-5 text-pink-500" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64">
                <nav className="mt-6 flex flex-col gap-2">
                  {links.map((link) => {
                    const Icon = link.icon;
                    const active = link.href === "/" ? pathname === "/" : pathname === link.href || pathname.startsWith(link.href + "/");

                    return (
                      <Link
                        key={link.href}
                        href={link.href}
                        className={cn(
                          "flex items-center gap-3 rounded-xl px-4 py-2 text-sm font-medium transition",
                          active ? "bg-pink-100/80 text-pink-600" : "text-slate-600 hover:bg-pink-50"
                        )}
                      >
                        <Icon className="h-4 w-4 text-pink-500" />
                        {link.label}
                      </Link>
                    );
                  })}
                </nav>
              </SheetContent>
            </Sheet>
          </div>

          <Suspense fallback={null}>
            <NavUser />
          </Suspense>
        </div>
      </nav>
    </header>
  );
}
