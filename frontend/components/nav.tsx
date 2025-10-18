"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTheme } from "next-themes"
import { Moon, Sun, Menu } from "lucide-react"
import { AppButton } from "@/components/app-button"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

type NavLink = {
  href: string
  label: string
}

const links: NavLink[] = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Upload" },
  { href: "/search", label: "Search" },
  { href: "/chat", label: "Chat" },
  { href: "/configuration", label: "Configuration" },
  { href: "/maintenance", label: "Maintenance" },
  { href: "/about", label: "About" },
]

export function Nav() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <header className="relative sticky top-0 z-50 shrink-0 border-b border-border/40 bg-background/50 backdrop-blur-xl">
      {/* Subtle gradient line at top */}
      <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-6">
          {/* Logo with enhanced styling */}
          <Link href="/" className="group flex shrink-0 items-center gap-3 transition-all">
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary/20 to-chart-4/20 opacity-0 blur-xl transition-opacity group-hover:opacity-100" />
              <div className="relative size-icon-3xl sm:h-14 sm:w-14 rounded-full bg-gradient-to-br from-primary/10 to-chart-4/10 p-2 ring-1 ring-primary/20 transition-all group-hover:ring-primary/40 group-hover:shadow-lg group-hover:shadow-primary/20">
                {mounted && (
                  <Image
                    src={
                      theme === "dark"
                        ? "/Snappy/snappy_dark_nobg_resized.png"
                        : "/Snappy/snappy_light_nobg_resized.png"
                    }
                    alt="Snappy"
                    width={48}
                    height={48}
                    className="object-contain transition-transform group-hover:scale-110"
                    priority
                  />
                )}
              </div>
            </div>
          </Link>

          {/* Desktop Navigation - Center */}
          <nav className="hidden flex-1 items-center justify-center gap-1 lg:flex">
            {links.map((link) => {
              const isActive =
                link.href === "/"
                  ? pathname === "/"
                  : pathname === link.href || pathname.startsWith(`${link.href}/`)

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "relative rounded-full px-5 py-2.5 text-body-sm font-medium transition-all duration-200 touch-manipulation",
                    isActive
                      ? "bg-primary/10 text-primary shadow-sm"
                      : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                  )}
                >
                  {isActive && (
                    <span className="absolute inset-0 rounded-full bg-gradient-to-r from-primary/5 to-purple-500/5 animate-pulse" />
                  )}
                  <span className="relative">{link.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {mounted && (
              <AppButton
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                iconShift
              >
                {theme === "dark" ? (
                  <Sun className="size-icon-lg transition-transform group-hover/app-button:rotate-45 group-hover/app-button:scale-110" />
                ) : (
                  <Moon className="size-icon-lg transition-transform group-hover/app-button:-rotate-12 group-hover/app-button:scale-110" />
                )}
                <span className="sr-only">Toggle theme</span>
              </AppButton>
            )}

            {/* Mobile Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild className="lg:hidden">
                <AppButton
                  variant="ghost"
                  size="icon"
                  iconShift
                >
                  <Menu className="size-icon-lg transition-transform group-hover/app-button:scale-110" />
                  <span className="sr-only">Open menu</span>
                </AppButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-56 rounded-2xl border-border/50 bg-card/95 backdrop-blur-xl"
              >
                {links.map((link) => {
                  const isActive =
                    link.href === "/"
                      ? pathname === "/"
                      : pathname === link.href || pathname.startsWith(`${link.href}/`)

                  return (
                    <DropdownMenuItem key={link.href} asChild>
                      <Link
                        href={link.href}
                        className={cn(
                          "w-full cursor-pointer rounded-xl px-3 py-2 text-body-sm transition-all",
                          isActive
                            ? "bg-primary/10 text-primary font-semibold"
                            : "hover:bg-muted/50"
                        )}
                      >
                        {link.label}
                      </Link>
                    </DropdownMenuItem>
                  )
                })}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  )
}
