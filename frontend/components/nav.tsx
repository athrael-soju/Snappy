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
import { useUploadStore } from "@/stores/app-store"

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
  const { uploading, uploadProgress } = useUploadStore()
  const showUploadBadge = uploading && typeof uploadProgress === "number"
  const uploadPercent = showUploadBadge
    ? Math.min(100, Math.max(0, Math.round(uploadProgress ?? 0)))
    : null

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <header className="relative sticky top-0 z-50 shrink-0 border-b border-vultr-blue-20/30 dark:border-vultr-light-blue/20 backdrop-blur-sm transition-colors">
      <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-vultr-blue via-vultr-light-blue to-vultr-blue-60" />

      <div className="layout-container flex items-center justify-between gap-6 py-3">
        <Link href="/" className="group flex shrink-0 items-center gap-3 transition-all">
          <div className="relative flex items-center">
            <div className="pointer-events-none absolute -inset-3 rounded-full bg-vultr-light-blue/25 opacity-0 blur-2xl transition-opacity duration-300 group-hover:opacity-100" />
            <div className="relative flex items-center justify-center">
              {mounted && (
                <Image
                  src={theme === "dark" ? "/brand/vultr-logo-reversed.svg" : "/brand/vultr-logo.svg"}
                  alt="Vultr"
                  width={136}
                  height={42}
                  priority
                  className="logo-min h-9 w-auto transition duration-200 group-hover:scale-105"
                />
              )}
            </div>
          </div>
        </Link>

        <nav className="hidden flex-1 items-center justify-center gap-2 lg:flex">
          {links.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname === link.href || pathname.startsWith(`${link.href}/`)
            const isUploadLink = link.href === "/upload"
            const shouldShowBadge = isUploadLink && showUploadBadge

            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "relative rounded-full px-4 py-2 text-body-xs font-light text-vultr-navy/80 transition-colors duration-200 hover:text-vultr-blue focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-vultr-light-blue focus-visible:ring-offset-2 focus-visible:ring-offset-transparent dark:text-white/70",
                  isActive ? "text-vultr-blue font-semibold dark:text-vultr-light-blue" : ""
                )}
              >
                {isActive && (
                  <span className="section-divider absolute inset-x-3 -bottom-1" />
                )}
                <span className="relative">{link.label}</span>
                {shouldShowBadge && uploadPercent !== null && (
                  <span className="absolute -top-2 -right-3 rounded-full bg-vultr-blue px-2 py-0.5 text-[10px] font-semibold text-white shadow-[var(--shadow-soft)]">
                    {uploadPercent}%
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        <div className="flex items-center gap-2">
          {mounted && (
            <AppButton
              variant="outline"
              size="icon-lg"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              iconShift
            >
              {theme === "dark" ? (
                <Sun className="size-icon-md transition-transform group-hover/app-button:rotate-45 group-hover/app-button:scale-110" />
              ) : (
                <Moon className="size-icon-md transition-transform group-hover/app-button:-rotate-12 group-hover/app-button:scale-110" />
              )}
              <span className="sr-only">Toggle theme</span>
            </AppButton>
          )}

          <div className="lg:hidden">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <AppButton variant="ghost" size="icon" iconShift>
                  <Menu className="size-icon-md transition-transform group-hover/app-button:scale-110" />
                  <span className="sr-only">Open menu</span>
                </AppButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-56 rounded-[var(--radius-card)] border border-vultr-blue-20/30 p-2 shadow-[var(--shadow-soft)] backdrop-blur-sm dark:border-vultr-light-blue/20"
              >
                {links.map((link) => {
                  const isActive =
                    link.href === "/"
                      ? pathname === "/"
                      : pathname === link.href || pathname.startsWith(`${link.href}/`)
                  const isUploadLink = link.href === "/upload"
                  const shouldShowBadge = isUploadLink && showUploadBadge

                  return (
                    <DropdownMenuItem key={link.href} asChild>
                      <Link
                        href={link.href}
                        className={cn(
                          "flex w-full cursor-pointer items-center justify-between gap-2 rounded-[calc(var(--radius-card)-0.5rem)] px-3 py-2 text-body-xs text-vultr-navy/80 transition-colors hover:bg-vultr-sky-blue/30 hover:text-vultr-blue dark:text-white/70",
                          isActive ? "bg-vultr-sky-blue/40 text-vultr-blue font-semibold dark:text-vultr-light-blue" : ""
                        )}
                      >
                        <span>{link.label}</span>
                        {shouldShowBadge && uploadPercent !== null && (
                          <span className="rounded-full bg-vultr-blue px-2 py-0.5 text-[10px] font-semibold text-white shadow-[var(--shadow-soft)]">
                            {uploadPercent}%
                          </span>
                        )}
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
