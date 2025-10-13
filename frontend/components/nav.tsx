"use client"

import { Suspense, useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { usePathname } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Home, Eye, CloudUpload, Brain, Menu } from "lucide-react"

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Sheet, SheetTrigger, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useAppStore } from '@/stores/app-store'
import { NavUser } from '@/components/nav-user'
import { ThemeSwitch } from '@/components/theme-switch'

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/search", label: "Retrieve", icon: Eye },
  { href: "/upload", label: "Add Docs", icon: CloudUpload },
  { href: "/chat", label: "Chat", icon: Brain },
] as const

const navContainerClasses =
  "rounded-full border border-border/60 bg-card/70 dark:bg-card/40 px-2 py-1 shadow-sm backdrop-blur-xl"
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
          className={cn(
            "h-4 w-4 transition-colors text-muted-foreground",
            active && "text-[color:var(--nav-pill-active-foreground,var(--foreground))]"
          )}
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
                "absolute -top-2 -right-2 flex h-[20px] min-w-[20px] items-center justify-center rounded-full border border-border/60 text-[10px] font-bold backdrop-blur",
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
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/95 supports-[backdrop-filter]:backdrop-blur-xl">
      <nav className="mx-auto flex h-16 max-w-5xl items-center gap-3 px-3 sm:px-6">
        <div className="flex flex-1 items-center justify-start min-w-0">
          <Link
            href="/"
            className="group flex items-center gap-3 rounded-full px-2 py-1 transition hover:bg-muted/40"
          >
            <span className="relative flex h-9 w-9 items-center justify-center sm:h-10 sm:w-10">
              <Image
                src="/Snappy/snappy_light_nobg_resized.png"
                alt="Snappy logo"
                width={40}
                height={40}
                className="block h-full w-full drop-shadow-sm transition-transform group-hover:scale-105 dark:hidden"
                priority
              />
              <Image
                src="/Snappy/snappy_dark_nobg_resized.png"
                alt="Snappy logo"
                width={40}
                height={40}
                className="hidden h-full w-full drop-shadow-sm transition-transform group-hover:scale-105 dark:block"
                priority
              />
            </span>
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
                  className="h-10 w-10 rounded-full border border-border/60 bg-card/70 text-[color:var(--nav-pill-inactive-foreground,var(--muted-foreground))] shadow-sm backdrop-blur-xl hover:text-[color:var(--nav-pill-hover-foreground,var(--foreground))]"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent
                side="left"
                className="w-72 border-border/60 bg-background/90 backdrop-blur-2xl p-0 flex flex-col"
              >
                <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                
                {/* Header Section */}
                <div className="px-6 pt-8 pb-6 border-b border-border/40">
                  <Link
                    href="/"
                    className="flex items-center gap-3 group"
                  >
                    <span className="relative flex h-12 w-12 items-center justify-center">
                      <Image
                        src="/Snappy/snappy_light_nobg_resized.png"
                        alt="Snappy logo"
                        width={48}
                        height={48}
                        className="block h-full w-full drop-shadow-lg transition-transform group-hover:scale-105 dark:hidden"
                        priority
                      />
                      <Image
                        src="/Snappy/snappy_dark_nobg_resized.png"
                        alt="Snappy logo"
                        width={48}
                        height={48}
                        className="hidden h-full w-full drop-shadow-lg transition-transform group-hover:scale-105 dark:block"
                        priority
                      />
                    </span>
                  </Link>
                </div>

                {/* Navigation Links */}
                <nav className="flex-1 px-4 py-6 flex flex-col gap-1.5 overflow-y-auto custom-scrollbar">
                  {links.map((link) => {
                    const Icon = link.icon
                    const active =
                      link.href === "/"
                        ? pathname === "/"
                        : pathname === link.href || pathname.startsWith(`${link.href}/`)
                    const indicator = link.href === "/upload" ? uploadIndicator() : null

                    return (
                      <Link
                        key={link.href}
                        href={link.href}
                        className={cn(
                          mobileLinkClasses,
                          "h-12 text-base gap-3 relative",
                          active ? mobileLinkActiveClasses : mobileLinkInactiveClasses
                        )}
                      >
                        <Icon
                          className={cn(
                            "h-5 w-5 transition-colors text-muted-foreground",
                            active && "text-[color:var(--nav-pill-active-foreground,var(--foreground))]"
                          )}
                        />
                        <span className="flex-1">{link.label}</span>
                        <AnimatePresence>
                          {indicator && (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.4, x: 8 }}
                              animate={{ opacity: 1, scale: 1, x: 0 }}
                              exit={{ opacity: 0, scale: 0.4, x: 8 }}
                              transition={{ duration: 0.25, type: "spring", stiffness: 280, damping: 20 }}
                              className={cn(
                                "flex h-6 min-w-[40px] items-center justify-center rounded-full border text-xs font-semibold backdrop-blur px-2",
                                indicator.isActive 
                                  ? "bg-primary/90 text-primary-foreground border-primary/40 shadow-sm" 
                                  : "bg-muted text-muted-foreground border-border/60"
                              )}
                            >
                              {indicator.count}%
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </Link>
                    )
                  })}
                </nav>

                {/* Footer Section */}
                <div className="px-4 py-4 border-t border-border/60 space-y-3 bg-card/70 dark:bg-card/30">
                  <div className="flex items-center justify-between px-2">
                    <span className="text-sm font-medium text-muted-foreground">Theme</span>
                    <ThemeSwitch />
                  </div>
                  <div className="pt-2">
                    <NavUser />
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>

          <div className="hidden sm:flex items-center gap-3">
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
