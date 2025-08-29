"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, Eye, CloudUpload, Brain, Shield, HelpCircle, User } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/8bit/dialog";
import AboutContent from "@/components/about-content";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/8bit/tooltip";
import { Button } from "@/components/ui/8bit/button";
import ThemeToggle from "@/components/theme-toggle";
import ProfileCard from "@/components/profile-card";

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-[var(--color-primary)]" },
  { href: "/search", label: "Search", icon: Eye, color: "text-[var(--color-primary)]" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-[var(--color-primary)]" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-[var(--color-accent)]" },
  { href: "/maintenance", label: "Maintenance", icon: Shield, color: "text-[var(--color-destructive)]" },
];

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  return (
    <header className="w-full border-b bg-card/60 backdrop-blur-xl supports-[backdrop-filter]:bg-card/50 sticky top-0 z-50 shadow-lg border-border/20">
      <nav className="mx-auto max-w-7xl flex items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-3 font-bold text-2xl tracking-tight hover:opacity-80 transition-all duration-300 hover:scale-105 group"
          >
            <Image
              src="/favicon.png"
              alt="App icon"
              width={40}
              height={40}
              className="transition-all duration-300 group-hover:rotate-3"
              priority
            />
            <span className="bg-gradient-to-r from-[var(--color-primary)] via-[var(--color-accent)] to-[var(--color-ring)] bg-clip-text text-transparent">
              FastAPI / Next.js / ColPali Template
            </span>
          </Link>
        </div>
        <div className="flex items-center gap-2">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname === link.href || pathname.startsWith(`${link.href}/`);
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-label={link.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-base font-medium transition-all duration-300 hover:scale-105 relative group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  active
                    ? "bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-[var(--color-primary-foreground)] shadow-lg hover:shadow-xl"
                    : "text-muted-foreground hover:text-foreground hover:bg-card/60 hover:shadow-md border border-transparent hover:border-[var(--color-border)]/50"
                )}
              >
                <Icon className={cn("w-6 h-6 relative z-10 transition-colors duration-300", active ? "text-[var(--color-primary-foreground)]" : link.color)} />
                <span className={cn("hidden sm:inline relative z-10 transition-colors duration-300", active ? "text-[var(--color-primary-foreground)] font-semibold" : "")}>
                  {link.label}
                </span>
              </Link>
            );
          })}
          {/* About dialog - placed before profile */}
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
                    <HelpCircle className="w-5 h-5 text-[var(--color-accent)] transition-colors duration-300 group-hover:text-[var(--color-ring)]" />
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

          {/* Profile dialog */}
          <Dialog open={profileOpen} onOpenChange={setProfileOpen}>
            <Tooltip>
              <TooltipTrigger asChild>
                <DialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Open profile"
                    className="group transition-transform hover:scale-105"
                  >
                    <User className="w-6 h-6 text-[var(--color-primary)] transition-colors duration-300 group-hover:text-[var(--color-ring)]" />
                    <span className="sr-only">Open profile</span>
                  </Button>
                </DialogTrigger>
              </TooltipTrigger>
              <TooltipContent>Profile</TooltipContent>
            </Tooltip>
            <DialogContent className="sm:max-w-md p-0 overflow-hidden">
              <DialogTitle className="sr-only">Profile</DialogTitle>
              <ProfileCard />
            </DialogContent>
          </Dialog>
        </div>
      </nav>
    </header>
  );
}
