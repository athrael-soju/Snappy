"use client"

import { useTheme } from "next-themes"
import { Toaster as Sonner, ToasterProps, toast as sonnerToast } from "sonner"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      closeButton={false}
      className="toaster group"
      style={
        {
          // Base toast styling
          "--normal-bg": "linear-gradient(135deg, var(--card) 0%, var(--muted) 100%)",
          "--normal-border": "var(--border)",
          "--normal-text": "var(--card-foreground)",
          
          // Success toasts - home page gradient: blue -> purple -> cyan
          "--success-bg": "linear-gradient(135deg, #2563eb 0%, #9333ea 50%, #0891b2 100%)",
          "--success-text": "white",
          "--success-border": "rgba(37, 99, 235, 0.3)",
          
          // Error toasts - red gradient with purple accent
          "--error-bg": "linear-gradient(135deg, #dc2626 0%, #be185d 50%, #b91c1c 100%)",
          "--error-text": "white", 
          "--error-border": "rgba(220, 38, 38, 0.3)",
          
          // Warning toasts - amber gradient with orange accent
          "--warning-bg": "linear-gradient(135deg, #d97706 0%, #ea580c 50%, #f59e0b 100%)",
          "--warning-text": "white",
          "--warning-border": "rgba(217, 119, 6, 0.3)",
          
          // Info toasts - cyan gradient with blue accent
          "--info-bg": "linear-gradient(135deg, #0891b2 0%, #0369a1 50%, #06b6d4 100%)",
          "--info-text": "white",
          "--info-border": "rgba(8, 145, 178, 0.3)",
          
          // Visual styling to match nav buttons
          "--border-radius": "0.75rem",
          "--box-shadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
          "--backdrop-filter": "blur(16px)",
        } as React.CSSProperties
      }
      toastOptions={{
        className: "rounded-xl shadow-lg backdrop-blur-xl border border-opacity-20 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl",
        style: {
          backdropFilter: "blur(16px)",
          borderRadius: "0.75rem",
        }
      }}
      {...props}
    />
  )
}

// Re-export toast function for consistency
const toast = sonnerToast

export { Toaster, toast }
