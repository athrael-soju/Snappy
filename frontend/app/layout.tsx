import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@/lib/api/client";
import { AppShell } from "@/components/layout";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "sonner";
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
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} text-foreground antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
          storageKey="colpali-theme"
        >
          {/* Animated gradient background */}
          <AnimatedBackground>
            <div className="relative">
              <NextTopLoader showSpinner={false} />
              <Toaster position="top-right" />
              <AppStoreProvider>
                <TooltipProvider>
                  <AppShell>{children}</AppShell>
                </TooltipProvider>
              </AppStoreProvider>
            </div>
          </AnimatedBackground>
        </ThemeProvider>
      </body>
    </html>
  );
}
