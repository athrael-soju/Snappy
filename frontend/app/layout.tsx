import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { AppStoreProvider } from "@/stores/app-store";
import { AnimatedBackground } from "@/components/animated-background";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Snappy!",
  description: "Snappy helps teams see their documents clearly with friendly visual search and chat.",
  icons: {
    icon: [
      { url: "/Snappy/snappy_light_nobg_resized.png", media: "(prefers-color-scheme: light)" },
      { url: "/Snappy/snappy_dark_nobg_resized.png", media: "(prefers-color-scheme: dark)" },
    ],
    shortcut: "/Snappy/snappy_light_nobg_resized.png",
    apple: "/Snappy/snappy_light_nobg_resized.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full">
      <body
        className={`${geistSans.variable} ${geistMono.variable} text-foreground antialiased relative h-full flex flex-col overflow-hidden`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
          storageKey="snappy-theme"
        >
          <AppStoreProvider>
            {/* Animated gradient background */}
            <AnimatedBackground>
              <div className="relative z-10 flex flex-1 flex-col min-h-0 h-full">
                <NextTopLoader showSpinner={false} />
                <Toaster richColors position="top-right" />
                <TooltipProvider>
                  <Nav />
                  <main className="flex-1 min-h-0 w-full flex flex-col">
                    {children}
                  </main>
                </TooltipProvider>
              </div>
            </AnimatedBackground>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
