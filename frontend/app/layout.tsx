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

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FastAPI / Next.js / ColPali Template",
  description: "Search, upload and chat with your visual documents",
  icons: {
    icon: "/favicon.png",
    shortcut: "/favicon.png",
    apple: "/favicon.png",
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
        className={`${geistSans.variable} ${geistMono.variable} bg-background text-foreground antialiased relative h-full flex flex-col overflow-hidden`}
      >
        {/* Site-wide background glow */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div
            aria-hidden
            className="absolute inset-x-0 top-[-10%] h-[60%] opacity-70 blur-3xl transition-opacity duration-500"
            style={{ background: "var(--backdrop-glow)" }}
          />
        </div>

        {/* Foreground content */}
        <div className="relative z-10 flex flex-1 flex-col min-h-0 overflow-hidden">
          <NextTopLoader showSpinner={false} />
          <Toaster richColors position="top-right" />
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
            storageKey="colpali-theme"
          >
            <AppStoreProvider>
              <TooltipProvider>
                <Nav />
                <main className="flex-1 min-h-0 w-full flex flex-col overflow-hidden">
                  {children}
                </main>
              </TooltipProvider>
            </AppStoreProvider>
          </ThemeProvider>
        </div>
      </body>
    </html>
  );
}
