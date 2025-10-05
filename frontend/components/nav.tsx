"use client";

import { Suspense, useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, Eye, CloudUpload, Brain, HelpCircle, Menu } from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/stores/app-store";
import { motion, AnimatePresence } from "framer-motion";
import { Sheet, SheetTrigger, SheetContent } from "@/components/ui/sheet";
import { useRouter } from "next/navigation";
import { NavUser } from "@/components/nav-user";

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-blue-600" },
  { href: "/search", label: "Search", icon: Eye, color: "text-blue-500" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-cyan-500" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-purple-500" },
];

export function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const { state } = useAppStore();
  const [showUploadBadge, setShowUploadBadge] = useState(true);

  const hasUploadProgress = state.upload.uploading || (state.upload.uploadProgress > 0 && state.upload.jobId);

  useEffect(() => {
    if (!state.upload.uploading && state.upload.uploadProgress >= 100 && !state.upload.jobId) {
      const timer = setTimeout(() => {
        setShowUploadBadge(false);
      }, 2500);
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

  const renderLink = (link: typeof links[number]) => {
    const active = link.href === "/" ? pathname === "/" : pathname === link.href || pathname.startsWith(`${link.href}/`);
    const Icon = link.icon;
    const uploadIndicator = link.href === "/upload" ? getUploadIndicator() : null;

    return (
      <Link
        key={link.href}
        href={link.href}
        className={cn(
          "relative flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition-colors",
          active
            ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow"
            : "text-muted-foreground hover:text-foreground hover:bg-blue-50"
        )}
      >
        <Icon className={cn("h-4 w-4", active ? "text-white" : link.color)} />
        <span className="hidden md:inline">{link.label}</span>
        <AnimatePresence>
          {uploadIndicator && (
            <motion.div
              initial={{ opacity: 0, scale: 0.3, y: -6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.3, y: -6 }}
              transition={{ duration: 0.25, type: "spring", stiffness: 260, damping: 18 }}
              className={cn(
                "absolute -top-1 -right-1 flex h-[20px] min-w-[20px] items-center justify-center rounded-full text-[10px] font-bold",
                uploadIndicator.isActive ? "bg-cyan-500 text-white shadow" : "bg-slate-600 text-white/90"
              )}
            >
              {uploadIndicator.count}%
            </motion.div>
          )}
        </AnimatePresence>
      </Link>
    );
  };

  return (
    <header className="sticky top-0 z-50 border-b border-blue-200/30 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/65">
      <nav className="mx-auto flex h-14 sm:h-16 max-w-6xl items-center justify-between px-3 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 sm:gap-3 font-semibold text-base sm:text-lg tracking-tight transition-opacity hover:opacity-80"
        >
          <Image
            src="/favicon.png"
            alt="App icon"
            width={32}
            height={32}
            className="h-8 w-8 sm:h-9 sm:w-9"
            priority
          />
          <span className="hidden md:inline bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent text-sm sm:text-base">
            FastAPI / Next.js / ColPali Template
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-2">
          {links.map(renderLink)}
        </div>

        <div className="flex items-center gap-1 sm:gap-2">
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Open navigation" className="h-9 w-9">
                  <Menu className="h-5 w-5 text-blue-600" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64">
                <nav className="mt-6 flex flex-col gap-2">
                  {links.map((link) => (
                    <div key={link.href}>
                      {renderLink(link)}
                    </div>
                  ))}
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
