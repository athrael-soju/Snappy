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
  title: "Snappy Template",
  description: "Snappy pairs FastAPI and Next.js so you can build visual AI tools fast.",
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
              <div className="flex min-h-screen flex-col">
                <Nav />
                <main className="flex-1 w-full">{children}</main>
              </div>
              <Toaster richColors position="top-right" />
            </TooltipProvider>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
