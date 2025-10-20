"use client"

import { useEffect, useMemo, useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  Menu, 
  Database, 
  Server, 
  HardDrive, 
  Network, 
  Container, 
  FileText, 
  Upload, 
  Search, 
  MessageSquare,
  Settings,
  Wrench,
  Info,
  ArrowRight,
  Sparkles,
  Cloud,
  Cpu
} from "lucide-react"

import { AppButton } from "@/components/app-button"
import { ThemeSwitcher } from "@/components/theme-switcher"
import { cn } from "@/lib/utils"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuIndicator,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  NavigationMenuViewport,
} from "@/components/ui/navigation-menu"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useUploadStore } from "@/stores/app-store"

type MenuLink = {
  label: string
  href: string
  description?: string
  external?: boolean
  showUploadProgress?: boolean
  icon?: any
}

type MenuCategory = {
  title: string
  icon?: any
  items: MenuLink[]
}

type NavSection = {
  label: string
  categories: MenuCategory[]
}

type PromoCard = {
  title: string
  description: string
  linkText: string
  linkHref: string
}

type BottomTab = {
  label: string
  href: string
  external?: boolean
}

const menuSections: NavSection[] = [
  {
    label: "Services",
    categories: [
      {
        title: "Core Services",
        icon: Sparkles,
        items: [
          {
            label: "Upload & Index",
            href: "/upload",
            description: "Process documents with ColPali vision models",
            icon: Upload,
            showUploadProgress: true,
          },
          {
            label: "Semantic Search",
            href: "/search",
            description: "Find documents using visual search",
            icon: Search,
          },
          {
            label: "Vision Chat",
            href: "/chat",
            description: "Chat with AI about your documents",
            icon: MessageSquare,
          },
        ],
      },
    ],
  },
  {
    label: "Maintenance",
    categories: [
      {
        title: "System Management",
        icon: Settings,
        items: [
          {
            label: "Configuration",
            href: "/configuration",
            description: "Optimize deployment settings",
            icon: Settings,
          },
          {
            label: "Maintenance",
            href: "/maintenance",
            description: "Monitor system health",
            icon: Wrench,
          },
        ],
      },
    ],
  },
]

const directLinks: MenuLink[] = [
  {
    label: "About",
    href: "/about",
    description: "Learn about Morty, your Visual Retrieval Buddy, and the technology behind the magic.",
    external: false,
  }
]

const promoCards: PromoCard[] = [
  {
    title: "Morty is part of the Vultr Cloud Alliance",
    description: "Accelerate Your AI and HPC Workloads with AMD or Vultr",
    linkText: "Learn more",
    linkHref: "https://www.vultr.com/partners/amd/",
  },
  {
    title: "Spend less than DO, get more.",
    description: "Get better performance, global reach, and more for less than DigitalOcean.",
    linkText: "Learn more",
    linkHref: "https://www.vultr.com/",
  },
]

const bottomTabs: BottomTab[] = [
  { label: "Resources", href: "https://www.vultr.com/resources/", external: true },
  { label: "Events", href: "https://www.vultr.com/events/", external: true },
  { label: "Support", href: "https://www.vultr.com/support/", external: true },
  { label: "Docs", href: "https://docs.vultr.com/", external: true },
  { label: "Community", href: "https://www.vultr.com/community/", external: true },
  { label: "Compliance", href: "https://www.vultr.com/legal/compliance/", external: true },
]

export function Nav() {
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const { uploading, uploadProgress } = useUploadStore()

  useEffect(() => {
    setMounted(true)
  }, [])

  const uploadPercent = useMemo(() => {
    if (!uploading || typeof uploadProgress !== "number") return null
    return Math.min(100, Math.max(0, Math.round(uploadProgress)))
  }, [uploading, uploadProgress])

  return (
    <header className="fixed top-0 z-50 w-full border-b border-[#1331a0]/40 bg-gradient-to-br from-[#06175a] via-[#0c2f95] to-[#1244cd] text-white shadow-[0_6px_18px_rgba(6,14,56,0.35)]">
      <div className="layout-container flex h-16 items-center gap-6 text-white">
        <Link href="/" className="group flex shrink-0 items-center justify-center gap-3" aria-label="Vultr home">
          <div className="relative flex items-center justify-center">
            <span className="pointer-events-none absolute -left-6 -right-6 -top-4 h-16 rounded-full bg-vultr-sky-blue/20 opacity-0 blur-2xl transition-opacity duration-300 " />
            {mounted && (
              <Image
                src="/brand/vultr-logo-reversed.svg"
                alt="Vultr"
                width={132}
                height={36}
                priority
                className="h-9 w-auto transition-transform duration-200 group-hover:scale-[1.02]"
              />
            )}
          </div>
        </Link>

        <NavigationMenu className="hidden flex-1 justify-center lg:flex">
          <NavigationMenuList className="gap-4">
            {menuSections.map((section) => (
              <NavigationMenuItem key={section.label}>
                <NavigationMenuTrigger className="rounded-full border border-transparent bg-transparent px-3 py-2 text-body-sm font-medium text-white/80 transition hover:text-white">
                  {section.label}
                </NavigationMenuTrigger>
                <NavigationMenuContent className="rounded-[var(--radius-card)] border border-white/10 bg-white/95 shadow-[0_18px_40px_-18px_rgba(8,24,80,0.75)] backdrop-blur-xl transition dark:bg-[#0b1f69]/95">
                  <div className="grid gap-6 p-6 sm:w-[750px] lg:grid-cols-[1fr_300px]">
                    {/* Main content area with categories */}
                    <div className="space-y-6">
                      {section.categories.map((category) => (
                        <div key={category.title} className="space-y-3">
                          <div className="flex items-center gap-2 text-body-xs font-semibold uppercase tracking-wide text-muted-foreground">
                            {category.icon && <category.icon className="size-icon-xs" />}
                            {category.title}
                          </div>
                          <ul className="grid gap-2">
                            {category.items.map((item) => (
                              <li key={item.label}>
                                <NavigationMenuLink asChild>
                                  <Link
                                    href={item.href}
                                    target={item.external ? "_blank" : undefined}
                                    rel={item.external ? "noreferrer noopener" : undefined}
                                    className={cn(
                                      "group flex items-start gap-3 rounded-lg border border-border/40 bg-background/50 px-3 py-2.5 text-left transition hover:border-primary/40 hover:bg-accent/50",
                                      pathname === item.href ? "border-primary/60 bg-accent" : ""
                                    )}
                                  >
                                    {item.icon && (
                                      <item.icon className="size-icon-sm mt-0.5 shrink-0 text-primary" />
                                    )}
                                    <div className="flex flex-1 flex-col gap-0.5">
                                      <span className="flex items-center gap-2 text-body-sm font-medium text-foreground">
                                        {item.label}
                                        {item.showUploadProgress && uploadPercent !== null && (
                                          <span className="rounded-sm bg-primary/20 px-1.5 py-0.5 text-body-xs font-medium text-primary">
                                            {uploadPercent}%
                                          </span>
                                        )}
                                      </span>
                                      {item.description && (
                                        <span className="text-body-xs text-muted-foreground">{item.description}</span>
                                      )}
                                    </div>
                                  </Link>
                                </NavigationMenuLink>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}

                      {/* Bottom tabs */}
                      <div className="border-t border-border/40 pt-4">
                        <div className="flex flex-wrap gap-2">
                          {bottomTabs.map((tab) => (
                            <Link
                              key={tab.label}
                              href={tab.href}
                              target={tab.external ? "_blank" : undefined}
                              rel={tab.external ? "noreferrer noopener" : undefined}
                              className="rounded-md px-3 py-1.5 text-body-xs font-medium text-primary transition hover:bg-accent"
                            >
                              {tab.label}
                            </Link>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Promotional sidebar */}
                    <div className="hidden lg:block">
                      <div className="space-y-4">
                        {promoCards.map((promo, index) => (
                          <div
                            key={index}
                            className="space-y-2 rounded-lg border border-primary/20 bg-primary/5 p-4"
                          >
                            <h4 className="text-body-sm font-semibold leading-snug text-foreground">
                              {promo.title}
                            </h4>
                            <p className="text-body-xs leading-relaxed text-muted-foreground">
                              {promo.description}
                            </p>
                            <Link
                              href={promo.linkHref}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="inline-flex items-center gap-1 text-body-xs font-medium text-primary transition hover:gap-2"
                            >
                              {promo.linkText}
                              <ArrowRight className="size-icon-2xs" />
                            </Link>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </NavigationMenuContent>
              </NavigationMenuItem>
            ))}

            {directLinks.map((link) => (
              <NavigationMenuItem key={link.label}>
                <NavigationMenuLink asChild>
                  <Link
                    href={link.href}
                    target={link.external ? "_blank" : undefined}
                    rel={link.external ? "noreferrer noopener" : undefined}
                    className="rounded-full px-3 py-2 text-body-sm font-medium text-white/80 transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-transparent"
                  >
                    {link.label}
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
          <NavigationMenuIndicator className="hidden lg:flex" />
          <NavigationMenuViewport className="rounded-[var(--radius-card)] border border-white/10 shadow-[0_18px_40px_-18px_rgba(8,24,80,0.75)]" />
        </NavigationMenu>

        <div className="ml-auto flex items-center gap-3">
          <ThemeSwitcher className="rounded-[var(--radius-button)] border border-white/20 text-white/80 hover:border-white/40 hover:bg-white/10 hover:text-white size-icon-xl" />
          <AppButton
            asChild
            variant="ghost"
            size="sm"
            className="hidden rounded-[var(--radius-button)] border border-white/20 text-body-sm font-medium text-white/80 hover:border-white/40 hover:bg-white/10 hover:text-white lg:inline-flex"
          >
            <Link href="https://my.vultr.com/" target="_blank" rel="noreferrer noopener">
              Sign In
            </Link>
          </AppButton>
          <AppButton
            asChild
            variant="primary"
            size="sm"
            className="hidden rounded-[var(--radius-button)] bg-white px-5 text-vultr-blue hover:bg-vultr-sky-blue/80 lg:inline-flex"
          >
            <Link href="https://www.vultr.com/company/contact/" target="_blank" rel="noreferrer noopener">
              Contact Sales
            </Link>
          </AppButton>
          <div className="lg:hidden">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <AppButton variant="outline" size="icon" className="rounded-[var(--radius-button)] border-white/30 bg-white/10 text-white hover:border-white/50 hover:bg-white/15">
                  <Menu className="size-icon-md" />
                  <span className="sr-only">Open navigation</span>
                </AppButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-72 rounded-[var(--radius-card)] border border-white/10 bg-[#0b1f69]/95 p-2 text-white shadow-[0_18px_40px_-18px_rgba(8,24,80,0.75)] backdrop-blur-xl"
              >
                {menuSections.map((section) => (
                  <div key={section.label} className="mb-3 last:mb-0">
                    <p className="px-3 pb-2 eyebrow text-white/50">
                      {section.label}
                    </p>
                    {section.categories.map((category) => (
                      <div key={category.title} className="mb-2">
                        <p className="px-3 pb-1.5 text-body-xs font-semibold uppercase tracking-wide text-white/40">
                          {category.title}
                        </p>
                        {category.items.map((item) => (
                          <DropdownMenuItem key={item.label} asChild>
                            <Link
                              href={item.href}
                              target={item.external ? "_blank" : undefined}
                              rel={item.external ? "noreferrer noopener" : undefined}
                              className={cn(
                                "flex w-full items-start gap-2 rounded-[var(--radius-button)] px-3 py-2 text-left text-body-sm text-white/80 transition hover:bg-white/10",
                                pathname === item.href ? "bg-white/10 text-white" : ""
                              )}
                            >
                              {item.icon && <item.icon className="size-icon-sm shrink-0" />}
                              <div className="flex flex-1 flex-col gap-0.5">
                                <span className="flex items-center gap-2 font-medium">
                                  {item.label}
                                  {item.showUploadProgress && uploadPercent !== null && (
                                    <span className="rounded-sm bg-white/20 px-1.5 py-0.5 text-body-xs font-medium text-white shadow-sm">
                                      {uploadPercent}%
                                    </span>
                                  )}
                                </span>
                                {item.description && (
                                  <span className="text-body-xs text-white/60">{item.description}</span>
                                )}
                              </div>
                            </Link>
                          </DropdownMenuItem>
                        ))}
                      </div>
                    ))}
                  </div>
                ))}

                {directLinks.length > 0 && (
                  <div className="mt-2 border-t border-white/10 pt-2">
                    {directLinks.map((link) => (
                      <DropdownMenuItem key={link.label} asChild>
                        <Link
                          href={link.href}
                          target={link.external ? "_blank" : undefined}
                          rel={link.external ? "noreferrer noopener" : undefined}
                          className="flex w-full items-center justify-between gap-2 rounded-[var(--radius-button)] px-3 py-2 text-body-sm font-medium text-white/80 transition hover:bg-white/10"
                        >
                          {link.label}
                        </Link>
                      </DropdownMenuItem>
                    ))}
                  </div>
                )}

                <div className="mt-3 flex flex-col gap-2">
                  <AppButton
                    asChild
                    variant="ghost"
                    size="sm"
                    className="w-full rounded-[var(--radius-button)] border border-transparent text-body-sm font-medium text-white/80 hover:border-white/40 hover:bg-white/10"
                  >
                    <Link href="https://my.vultr.com/" target="_blank" rel="noreferrer noopener">
                      Sign In
                    </Link>
                  </AppButton>
                  <AppButton
                    asChild
                    variant="primary"
                    size="sm"
                    className="w-full rounded-[var(--radius-button)] bg-white px-5 text-vultr-blue hover:bg-vultr-sky-blue/80"
                  >
                    <Link href="https://www.vultr.com/company/contact/" target="_blank" rel="noreferrer noopener">
                      Contact Sales
                    </Link>
                  </AppButton>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  )
}
