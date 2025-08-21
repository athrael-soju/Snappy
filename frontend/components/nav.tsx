"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home" },
  { href: "/search", label: "Search" },
  { href: "/upload", label: "Upload" },
  { href: "/chat", label: "Chat" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="w-full border-b border-black/10 dark:border-white/10 sticky top-0 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-40">
      <nav className="mx-auto max-w-6xl flex items-center justify-between gap-4 p-4 text-sm">
        <Link href="/" className="font-semibold tracking-tight">
          ColPali UI
        </Link>
        <div className="flex items-center gap-2">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "px-3 py-1.5 rounded-md transition-colors",
                  active
                    ? "bg-black text-white dark:bg-white dark:text-black"
                    : "hover:bg-black/5 dark:hover:bg-white/10"
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
