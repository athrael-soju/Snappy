"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, Eye, CloudUpload, Brain, Shield, HelpCircle } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/8bit/dialog";
import AboutContent from "@/components/about-content";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/8bit/tooltip";
import { Button } from "@/components/ui/8bit/button";

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-blue-600" },
  { href: "/search", label: "Search", icon: Eye, color: "text-blue-500" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-green-500" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-purple-500" },
  { href: "/maintenance", label: "Maintenance", icon: Shield, color: "text-red-500" },
];

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="w-full border-b bg-gradient-to-r from-blue-50/80 via-purple-50/60 to-cyan-50/80 backdrop-blur-xl supports-[backdrop-filter]:bg-gradient-to-r supports-[backdrop-filter]:from-blue-50/60 supports-[backdrop-filter]:via-purple-50/40 supports-[backdrop-filter]:to-cyan-50/60 sticky top-0 z-50 shadow-lg border-blue-200/20">
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
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
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
                  "flex items-center gap-2 px-4 py-2.5 rounded-xl text-base font-medium transition-all duration-300 hover:scale-105 relative group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  active
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:shadow-xl"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/60 hover:shadow-md border border-transparent hover:border-blue-200/50"
                )}
                >
                <Icon className={cn("w-6 h-6 relative z-10 transition-colors duration-300", active ? "text-white" : link.color)} />
                <span className={cn("hidden sm:inline relative z-10 transition-colors duration-300", active ? "text-white font-semibold" : "")}> 
                  {link.label}
                </span>
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
                    <HelpCircle className="w-5 h-5 text-blue-600 transition-colors duration-300 group-hover:text-cyan-600" />
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
        </div>
      </nav>
    </header>
  );
}
