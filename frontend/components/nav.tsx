"use client"

import { Suspense, useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { usePathname } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Home, Eye, CloudUpload, Brain, Menu } from "lucide-react"

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Sheet, SheetTrigger, SheetContent } from '@/components/ui/sheet'
import { useAppStore } from '@/stores/app-store'
import { NavUser } from '@/components/nav-user'
import { ThemeSwitch } from '@/components/theme-switch'

const links = [
  { href: "/", label: "Home", icon: Home, color: "text-primary" },
  { href: "/search", label: "Search", icon: Eye, color: "text-secondary" },
  { href: "/upload", label: "Upload", icon: CloudUpload, color: "text-accent" },
  { href: "/chat", label: "Chat", icon: Brain, color: "text-destructive" },
] as const

const navContainerClasses =
  "rounded-full border border-border/40 bg-card/60 px-1.5 py-1 shadow-[0_2px_18px_rgba(0,0,0,0.12)] backdrop-blur-xl"
const navLinkClasses = "nav-pill text-[color:var(--nav-pill-inactive-foreground,var(--muted-foreground))]"
const navLinkActiveClasses = "nav-pill-active text-[color:var(--nav-pill-active-foreground,var(--foreground))] font-semibold"

const mobileLinkClasses = "nav-pill w-full justify-start text-base"
const mobileLinkActiveClasses = "nav-pill-active text-[color:var(--nav-pill-active-foreground,var(--foreground))] font-semibold"
const mobileLinkInactiveClasses = "text-[color:var(--nav-pill-inactive-foreground,var(--muted-foreground))] hover:text-[color:var(--nav-pill-hover-foreground,var(--foreground))]"

export function Nav() {
  const pathname = usePathname()
  const { state } = useAppStore()
  const [showUploadBadge, setShowUploadBadge] = useState(true)

  const hasUploadProgress =
    state.upload.uploading || (state.upload.uploadProgress > 0 && state.upload.jobId)

  useEffect(() => {
    if (!state.upload.uploading && state.upload.uploadProgress >= 100 && !state.upload.jobId) {
      const timer = setTimeout(() => setShowUploadBadge(false), 2400)
      return () => clearTimeout(timer)
    }

    if (state.upload.uploading || (state.upload.uploadProgress < 100 && state.upload.jobId)) {
      setShowUploadBadge(true)
    } else if (!state.upload.jobId && state.upload.uploadProgress === 0) {
      setShowUploadBadge(false)
    }
  }, [state.upload.uploading, state.upload.uploadProgress, state.upload.jobId])

  const uploadIndicator = () => {
    if (hasUploadProgress && showUploadBadge) {
      return {
        count: Math.round(state.upload.uploadProgress),
        isActive: state.upload.uploading,
      }
    }

    return null
  }

  const renderLink = (link: (typeof links)[number]) => {
    const active =
      link.href === "/"
        ? pathname === "/"
        : pathname === link.href || pathname.startsWith(`${link.href}/`)

    const Icon = link.icon
    const indicator = link.href === "/upload" ? uploadIndicator() : null

    return (
      <Link
        key={link.href}
        href={link.href}
        className={cn(navLinkClasses, active && navLinkActiveClasses)}
      >
        <Icon
          className={cn("h-4 w-4 transition-colors", active ? "text-[color:var(--nav-pill-active-foreground,var(--foreground))]" : link.color)}
        />
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
                indicator.isActive ? "bg-primary text-primary-foreground shadow" : "bg-card text-foreground/90"
              )}
            >
              {indicator.count}%
            </motion.div>
          )}
        </AnimatePresence>
      </Link>
    )
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 supports-[backdrop-filter]:backdrop-blur-2xl">
      <nav className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-3 sm:px-6">
        <div className="flex flex-1 items-center justify-start min-w-0">
          <Link
            href="/"
            className="group flex items-center gap-2 sm:gap-3 rounded-full px-2 py-1 transition hover:bg-[color:var(--nav-pill-hover)]"
          >
            <Image
              src="/favicon.png"
              alt="App icon"
              width={40}
              height={40}
              className="h-9 w-9 sm:h-10 sm:w-10 drop-shadow-sm"
              priority
            />
          </Link>
        </div>

        <div className="hidden md:flex flex-none items-center justify-center">
          <div className={navContainerClasses}>
            <div className="flex items-center gap-1">
              {links.map(renderLink)}
            </div>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-end gap-2">
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Open navigation"
                  className="h-10 w-10 rounded-full border border-border/50 bg-card/80 text-[color:var(--nav-pill-inactive-foreground,var(--muted-foreground))] shadow-sm hover:text-[color:var(--nav-pill-hover-foreground,var(--foreground))]"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 border-border/40 bg-background/95">
                <nav className="mt-6 flex flex-col gap-2">
                  {links.map((link) => {
                    const Icon = link.icon
                    const active =
                      link.href === "/"
                        ? pathname === "/"
                        : pathname === link.href || pathname.startsWith(`${link.href}/`)

                    return (
                      <Link
                        key={link.href}
                        href={link.href}
                        className={cn(
                          mobileLinkClasses,
                          active ? mobileLinkActiveClasses : mobileLinkInactiveClasses
                        )}
                      >
                        <Icon
                          className={cn("h-4 w-4 transition-colors", active ? "text-[color:var(--nav-pill-active-foreground,var(--foreground))]" : link.color)}
                        />
                        {link.label}
                      </Link>
                    )
                  })}
                </nav>
              </SheetContent>
            </Sheet>
          </div>

          <div className="hidden sm:block">
            <ThemeSwitch />
          </div>

          <Suspense fallback={null}>
            <NavUser />
          </Suspense>
        </div>
      </nav>
    </header>
  )
}
