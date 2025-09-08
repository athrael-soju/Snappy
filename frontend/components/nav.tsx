"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, Eye, CloudUpload, Brain, Shield, HelpCircle } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import AboutContent from "@/components/about-content";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useAppStore } from "@/stores/app-store";
import { motion, AnimatePresence } from "framer-motion";

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-primary" },
  { href: "/search", label: "Search", icon: Eye, color: "text-primary" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-primary" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-primary" },
  { href: "/maintenance", label: "Maintenance", icon: Shield, color: "text-destructive" },
];

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { state } = useAppStore();
  const [showUploadBadge, setShowUploadBadge] = useState(true);

  // Check for upload progress only
  const hasUploadProgress = state.upload.uploading || (state.upload.uploadProgress > 0 && state.upload.jobId);

  // Auto-hide upload badge when upload completes
  useEffect(() => {
    if (!state.upload.uploading && state.upload.uploadProgress >= 100 && !state.upload.jobId) {
      const timer = setTimeout(() => {
        setShowUploadBadge(false);
      }, 3000); // Hide after 3 seconds when upload completes
      return () => clearTimeout(timer);
    } else if (state.upload.uploading || (state.upload.uploadProgress < 100 && state.upload.jobId)) {
      // Show badge when upload is active or incomplete
      setShowUploadBadge(true);
    } else if (!state.upload.jobId && state.upload.uploadProgress === 0) {
      // Hide badge when no job and no progress
      setShowUploadBadge(false);
    }
  }, [state.upload.uploading, state.upload.uploadProgress, state.upload.jobId]);

  const getUploadIndicator = () => {
    if (hasUploadProgress && showUploadBadge) {
      return {
        count: Math.round(state.upload.uploadProgress),
        isActive: state.upload.uploading
      };
    }
    return null;
  };
  return (
    <header className="w-full border-b bg-gradient-to-r from-primary/10 via-secondary/10 to-primary/10 backdrop-blur-xl supports-[backdrop-filter]:bg-gradient-to-r supports-[backdrop-filter]:from-primary/5 supports-[backdrop-filter]:via-secondary/5 supports-[backdrop-filter]:to-primary/5 sticky top-0 z-50 shadow-lg border-border">
      <nav className="mx-auto max-w-6xl flex items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-3 font-bold text-xl tracking-tight hover:opacity-80 transition-all duration-300 hover:scale-105 group"
          >
            <Image
              src="/favicon.png"
              alt="App icon"
              width={40}
              height={40}
              className="transition-all duration-300 group-hover:rotate-3"
              priority
            />
            <span className="bg-gradient-to-r from-primary via-primary to-primary bg-clip-text text-transparent">
              FastAPI / Next.js / ColPali Template
            </span>
          </Link>
        </div>
        <div className="flex items-center gap-2">
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
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 hover:scale-105 relative group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  active
                    ? "bg-gradient-to-r from-primary to-primary text-primary-foreground shadow-lg hover:shadow-xl"
                    : "text-muted-foreground hover:text-foreground hover:bg-background/60 hover:shadow-md border border-transparent hover:border-border",
                  // Add extra padding-right when badge is present to prevent overlap
                  uploadIndicator && link.href === "/upload" && "pr-8"
                )}
              >
                <Icon className={cn("w-4 h-4 relative z-10 transition-colors duration-300", active ? "text-primary-foreground" : link.color)} />
                <span className={cn("hidden sm:inline relative z-10 transition-colors duration-300", active ? "text-primary-foreground font-semibold" : "")}>
                  {link.label}
                </span>
                {/* Upload progress badge */}
                <AnimatePresence>
                  {uploadIndicator && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.3, y: -10 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.3, y: -10 }}
                      transition={{ duration: 0.3, type: "spring", stiffness: 300, damping: 20 }}
                      className={cn(
                        "absolute -top-1 -right-1 text-xs font-bold rounded-full min-w-[22px] h-[22px] flex items-center justify-center transition-all duration-300 z-20",
                        // Enhanced styling to match the app theme
                        uploadIndicator.isActive
                          ? "bg-gradient-to-br from-primary via-primary to-primary text-primary-foreground shadow-lg shadow-primary/40 border-2 border-primary-foreground/80"
                          : "bg-gradient-to-br from-muted via-muted to-muted text-muted-foreground shadow-md border-2 border-primary-foreground/60",
                        "hover:scale-110 hover:shadow-xl",
                        // Subtle backdrop blur for premium feel
                        "backdrop-blur-sm"
                      )}
                      title={`Upload ${uploadIndicator.count}% complete`}
                    >
                      {/* Animated progress ring background */}
                      {uploadIndicator.isActive && (
                        <motion.div
                          className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/30 to-primary/30"
                          animate={{
                            scale: [1, 1.15, 1],
                            opacity: [0.3, 0.6, 0.3]
                          }}
                          transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: "easeInOut"
                          }}
                        />
                      )}

                      {/* Progress text with smooth transitions */}
                      <motion.span
                        key={`upload-${uploadIndicator.count}`}
                        initial={{ scale: 1.3, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ duration: 0.2, type: "spring", stiffness: 400 }}
                        className="relative z-10 text-[10px] font-extrabold tracking-tight"
                      >
                        {uploadIndicator.count}%
                      </motion.span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Link>
            );
          })}

          <Dialog open={open} onOpenChange={setOpen}>
            <Tooltip>
              <TooltipTrigger asChild>
                <DialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="About this template"
                    className="group transition-transform hover:scale-105"
                  >
                    <HelpCircle className="w-5 h-5 text-primary transition-colors duration-300 group-hover:text-primary/80" />
                    <span className="sr-only">About this template</span>
                  </Button>
                </DialogTrigger>
              </TooltipTrigger>
              <TooltipContent>About this template</TooltipContent>
            </Tooltip>
            <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-3xl">
              <DialogTitle className="flex items-center gap-2 text-lg" />
              <AboutContent onClose={() => setOpen(false)} />
            </DialogContent>
          </Dialog>
          <ThemeToggle />
        </div>
      </nav>
    </header>
  );
}
