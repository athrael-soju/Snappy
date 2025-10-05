"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, Eye, CloudUpload, Brain, HelpCircle } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import AboutContent from "@/components/about-content";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/stores/app-store";
import { motion, AnimatePresence } from "framer-motion";
import { NavUser } from "@/components/nav-user";

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-blue-600" },
  { href: "/search", label: "Search", icon: Eye, color: "text-blue-500" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-cyan-500" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-purple-500" },
];

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { state } = useAppStore();
  const [showUploadBadge, setShowUploadBadge] = useState(true);

  const hasUploadProgress = state.upload.uploading || (state.upload.uploadProgress > 0 && state.upload.jobId);

  useEffect(() => {
    if (!state.upload.uploading && state.upload.uploadProgress >= 100 && !state.upload.jobId) {
      const timer = setTimeout(() => {
        setShowUploadBadge(false);
      }, 3000);
      return () => clearTimeout(timer);
    } else if (state.upload.uploading || (state.upload.uploadProgress < 100 && state.upload.jobId)) {
      setShowUploadBadge(true);
    } else if (!state.upload.jobId && state.upload.uploadProgress === 0) {
      setShowUploadBadge(false);
    }
  }, [state.upload.uploading, state.upload.uploadProgress, state.upload.jobId]);

  const getUploadIndicator = () => {
    if (hasUploadProgress && showUploadBadge) {
      return {
        count: Math.round(state.upload.uploadProgress),
        isActive: state.upload.uploading,
      };
    }
    return null;
  };

  return (
    <header className="sticky top-0 z-50 border-b border-blue-200/20 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 shadow-sm">
      <nav className="mx-auto flex h-14 sm:h-16 max-w-6xl items-center justify-between gap-2 px-3 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 sm:gap-3 font-bold text-base sm:text-lg tracking-tight transition-all duration-300 hover:opacity-80"
        >
          <Image
            src="/favicon.png"
            alt="App icon"
            width={32}
            height={32}
            className="w-8 h-8 sm:w-9 sm:h-9"
            priority
          />
          <span className="hidden md:inline bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent text-sm sm:text-base md:text-lg">
            FastAPI / Next.js / ColPali Template
          </span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-3">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname === link.href || pathname.startsWith(`${link.href}/`);
            const Icon = link.icon;
            const uploadIndicator = link.href === "/upload" ? getUploadIndicator() : null;
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-label={link.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex items-center gap-1.5 sm:gap-2 rounded-full px-2.5 py-1.5 sm:px-4 sm:py-2 text-xs sm:text-sm font-medium transition-all",
                  active
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow"
                    : "text-muted-foreground hover:text-foreground hover:bg-blue-50",
                  uploadIndicator && link.href === "/upload" && "pr-5 sm:pr-8"
                )}
              >
                <Icon className={cn("w-4 h-4 sm:w-4 sm:h-4", active ? "text-white" : link.color)} />
                <span className="hidden sm:inline">{link.label}</span>
                <AnimatePresence>
                  {uploadIndicator && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.3, y: -6 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.3, y: -6 }}
                      transition={{ duration: 0.25, type: "spring", stiffness: 260, damping: 18 }}
                      className={cn(
                        "absolute -top-1 -right-1 flex h-[20px] min-w-[20px] items-center justify-center rounded-full text-[10px] font-bold",
                        uploadIndicator.isActive
                          ? "bg-cyan-500 text-white shadow"
                          : "bg-slate-600 text-white/90"
                      )}
                    >
                      {uploadIndicator.count}%
                    </motion.div>
                  )}
                </AnimatePresence>
              </Link>
            );
          })}

          <NavUser />

          <Dialog open={open} onOpenChange={setOpen}>
            <Tooltip>
              <TooltipTrigger asChild>
                <DialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="About this template"
                    className="h-9 w-9 sm:h-10 sm:w-10"
                  >
                    <HelpCircle className="h-5 w-5 text-blue-600" />
                    <span className="sr-only">About this template</span>
                  </Button>
                </DialogTrigger>
              </TooltipTrigger>
              <TooltipContent>About this template</TooltipContent>
            </Tooltip>
            <DialogContent className="max-h-[90vh] max-w-[95vw] sm:max-w-4xl overflow-y-auto">
              <DialogTitle className="flex items-center gap-2 text-lg" />
              <AboutContent onClose={() => setOpen(false)} />
            </DialogContent>
          </Dialog>
        </div>
      </nav>
    </header>
  );
}
