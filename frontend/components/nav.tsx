"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

type NavLink = {
  href: string;
  label: string;
};

const links: NavLink[] = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Upload" },
  { href: "/search", label: "Search" },
  { href: "/chat", label: "Chat" },
  { href: "/configuration", label: "Configuration" },
  { href: "/maintenance", label: "Maintenance" },
  { href: "/about", label: "About" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-wrap items-center justify-between gap-4">
      <Link href="/" className="text-lg font-semibold tracking-tight text-foreground">
        ColPali Template
      </Link>
      <div className="flex flex-wrap gap-2 text-sm">
        {links.map((link) => {
          const isActive =
            link.href === "/"
              ? pathname === "/"
              : pathname === link.href || pathname.startsWith(`${link.href}/`);

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-3 py-1.5 font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
