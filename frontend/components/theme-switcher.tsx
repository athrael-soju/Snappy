"use client"

"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

import { AppButton } from "@/components/app-button"
import { cn } from "@/lib/utils"

type ThemeSwitcherProps = {
  /**
   * Optional classes merged into the toggle button.
   */
  className?: string
  /**
   * Optional classes merged into both icons.
   */
  iconClassName?: string
}

export function ThemeSwitcher({ className, iconClassName }: ThemeSwitcherProps) {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark")
  }

  return (
    <AppButton
      variant="ghost"
      size="icon-sm"
      onClick={toggleTheme}
      className={cn(
        "relative overflow-hidden text-vultr-blue hover:bg-vultr-sky-blue/40 hover:text-vultr-blue",
        "dark:text-white/80 dark:hover:text-white",
        className
      )}
      aria-label="Toggle theme"
    >
      <Sun
        className={cn(
          "h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0",
          iconClassName
        )}
      />
      <Moon
        className={cn(
          "absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100",
          iconClassName
        )}
      />
    </AppButton>
  )
}

export type { ThemeSwitcherProps }
