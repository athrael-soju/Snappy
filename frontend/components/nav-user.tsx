"use client"

import { type CSSProperties } from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { UserCircle, SlidersHorizontal, Database, Info } from "lucide-react"

const triggerBaseClasses =
  "group relative h-11 w-11 sm:h-12 sm:w-12 rounded-full border border-border/50 bg-card/80 text-muted-foreground shadow-sm transition-all"
const triggerActiveClasses = "shadow-lg ring-2 ring-primary/30"
const triggerHoverClasses = "hover:text-foreground hover:shadow-md"

const itemClasses =
  "mx-1 flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition text-muted-foreground hover:bg-[color:var(--nav-pill-hover)] hover:text-foreground"

const menuActiveStyle = (isActive: boolean): CSSProperties | undefined =>
  isActive
    ? {
        backgroundImage: "var(--nav-pill-active)",
        color: "var(--foreground)",
        boxShadow: "var(--nav-pill-shadow)",
      }
    : undefined

export function NavUser() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const maintenanceActive = pathname.startsWith("/maintenance")
  const aboutActive = pathname.startsWith("/about")
  const dropdownActive = maintenanceActive || aboutActive
  const section = searchParams.get("section") === "data" ? "data" : "configuration"

  const navigate = (target: "configuration" | "data") => {
    const params = new URLSearchParams()
    params.set("section", target)
    router.push(`/maintenance?${params.toString()}`)
  }

  const maintenanceItems = [
    {
      key: "configuration",
      label: "Configuration",
      icon: SlidersHorizontal,
      isActive: maintenanceActive && section === "configuration",
      action: () => navigate("configuration"),
    },
    {
      key: "data",
      label: "Data Management",
      icon: Database,
      isActive: maintenanceActive && section === "data",
      action: () => navigate("data"),
    },
  ] as const

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open maintenance menu"
          className={cn(triggerBaseClasses, dropdownActive ? triggerActiveClasses : triggerHoverClasses)}
        >
          <span
            className={cn(
              "flex h-full w-full items-center justify-center rounded-full transition-colors",
              dropdownActive ? "text-white dark:text-foreground" : "bg-transparent"
            )}
            style={dropdownActive ? { backgroundImage: "var(--nav-pill-active)" } : undefined}
          >
            <UserCircle className="h-6 w-6" />
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        sideOffset={12}
        className="w-56 rounded-2xl border border-border/50 bg-card/95 backdrop-blur-xl shadow-xl"
      >
        <DropdownMenuLabel className="px-3 pt-2 text-[11px] font-semibold uppercase tracking-[0.35em] text-muted-foreground">
          System
        </DropdownMenuLabel>
        {maintenanceItems.map((item) => (
          <DropdownMenuItem
            key={item.key}
            onSelect={(event) => {
              event.preventDefault()
              item.action()
            }}
            className={cn(itemClasses, item.isActive && "font-semibold")}
            style={menuActiveStyle(item.isActive)}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator className="my-2 bg-border/60" />
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault()
            router.push("/about")
          }}
          className={cn(itemClasses, aboutActive && "font-semibold")}
          style={menuActiveStyle(aboutActive)}
        >
          <Info className="h-4 w-4" />
          About this Template
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
