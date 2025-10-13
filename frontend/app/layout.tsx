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
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-background text-foreground antialiased`}
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
              <div className="flex min-h-screen flex-col">
                <NextTopLoader showSpinner={false} />
                <Toaster richColors position="top-right" />
                <Nav />
                <main className="flex-1 flex flex-col">
                  {children}
                </main>
              </div>
            </TooltipProvider>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}


