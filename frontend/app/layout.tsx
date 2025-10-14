"use client";

import { useState } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@/lib/api/client";
import { SidebarNav } from "@/components/sidebar-nav";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { AppStoreProvider } from "@/stores/app-store";
import { cn } from "@/lib/utils";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>Snappy Template</title>
        <meta name="description" content="Snappy pairs FastAPI and Next.js so you can build visual AI tools fast." />
        <link rel="icon" href="/favicon.png" />
        <link rel="shortcut icon" href="/favicon.png" />
        <link rel="apple-touch-icon" href="/favicon.png" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} bg-background text-foreground antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
          storageKey="snappy-theme"
        >
          <AppStoreProvider>
            <TooltipProvider>
              <NextTopLoader showSpinner={false} height={3} />
              <div className="flex min-h-screen">
                <SidebarNav 
                  collapsed={sidebarCollapsed} 
                  onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)} 
                />
                <main 
                  className={cn(
                    "flex-1 transition-all duration-300",
                    sidebarCollapsed ? "ml-16" : "ml-64"
                  )}
                >
                  {children}
                </main>
              </div>
              <Toaster richColors position="top-right" />
            </TooltipProvider>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
