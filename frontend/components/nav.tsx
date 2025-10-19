"use client"

import { useEffect, useMemo, useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu } from "lucide-react"

import { AppButton } from "@/components/app-button"
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
  description: string
  external?: boolean
  showUploadProgress?: boolean
}

type NavSection = {
  label: string
  items: MenuLink[]
}

const menuSections: NavSection[] = [
  {
    label: "Services",
    items: [
      {
        label: "Upload & Index",
        href: "/upload",
        description: "Ingest and process documents with ColPali-powered vision models.",
        showUploadProgress: true,
      },
      {
        label: "Semantic Search",
        href: "/search",
        description: "Find relevant documents instantly using advanced vector search techniques.",
      },
      {
        label: "Vision Chat",
        href: "/chat",
        description: "Interact with your documents through an AI-powered chat interface.",
      },
    ],
  },
  {
    label: "Management",
    items: [
      {
        label: "Configuration",
        href: "/configuration",
        description: "Customize and optimize your ColPali deployment settings easily.",
      },
      {
        label: "Maintenance",
        href: "/maintenance",
        description: "Monitor system health and manage updates for seamless operation.",
      },
    ],
  }
]

const directLinks: MenuLink[] = [
  {
    label: "About",
    href: "/about",
    description: "Understand the brand system and roadmap behind this template.",
    external: false,
  }
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
        <Link href="/" className="group flex shrink-0 items-center justify-center" aria-label="Vultr home">
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
                <NavigationMenuContent className="rounded-[var(--radius-card)] border border-white/10 bg-[#0b1f69]/95 p-4 shadow-[0_18px_40px_-18px_rgba(8,24,80,0.75)] backdrop-blur-xl transition">
                  <ul className="grid gap-2 sm:w-[400px]">
                    {section.items.map((item) => (
                      <li key={item.label}>
                        <NavigationMenuLink asChild>
                          <Link
                            href={item.href}
                            target={item.external ? "_blank" : undefined}
                            rel={item.external ? "noreferrer noopener" : undefined}
                            className={cn(
                              "group flex flex-col gap-1 rounded-[var(--radius-card)] border border-white/10 bg-white/5 px-4 py-3 text-left transition hover:-translate-y-0.5 hover:border-white/30 hover:bg-white/10",
                              pathname === item.href ? "border-white/40 bg-white/10" : ""
                            )}
                          >
                            <span className="flex items-center gap-2 text-body-sm font-medium text-white group-hover:text-white">
                              {item.label}
                              {item.showUploadProgress && uploadPercent !== null && (
                                <span className="rounded-sm bg-white/20 px-1.5 py-0.5 text-body-xs font-medium text-white shadow-sm">
                                  {uploadPercent}%
                                </span>
                              )}
                            </span>
                            {item.description && (
                              <span className="text-body-xs text-white/70">{item.description}</span>
                            )}
                          </Link>
                        </NavigationMenuLink>
                      </li>
                    ))}
                  </ul>
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
                  <div key={section.label} className="mb-2 last:mb-0">
                    <p className="px-3 pb-2 eyebrow text-white/50">
                      {section.label}
                    </p>
                    {section.items.map((item) => (
                      <DropdownMenuItem key={item.label} asChild>
                        <Link
                          href={item.href}
                          target={item.external ? "_blank" : undefined}
                          rel={item.external ? "noreferrer noopener" : undefined}
                          className={cn(
                            "flex w-full flex-col gap-1 rounded-[var(--radius-button)] px-3 py-2 text-left text-body-sm text-white/80 transition hover:bg-white/10",
                            pathname === item.href ? "bg-white/10 text-white" : ""
                          )}
                        >
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
                        </Link>
                      </DropdownMenuItem>
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
