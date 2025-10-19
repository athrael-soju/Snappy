import type { Metadata } from "next";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { Toaster } from "@/components/ui/sonner";
import { AppStoreProvider } from "@/stores/app-store";
import { ThemeProvider } from "@/components/theme-provider";
import NextTopLoader from "nextjs-toploader";

export const metadata: Metadata = {
  title: "Vultr Vision",
  description:
    "Deploy Vultr's ColPali-powered document intelligence across your global infrastructure. Upload, search, and collaborate with Vultr's signature performance.",
  icons: {
    icon: "/brand/signet__on-white.svg",
    shortcut: "/brand/signet__on-white.svg",
    apple: "/brand/signet__on-white.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
        />
      </head>
      <body className="min-h-screen bg-white font-sans text-vultr-navy antialiased dark:bg-vultr-midnight dark:text-white">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <NextTopLoader
            color="var(--color-vultr-blue)"
            initialPosition={0.12}
            crawlSpeed={250}
            height={3}
            crawl
            showSpinner={false}
            easing="ease"
            speed={240}
            shadow="0 0 18px color-mix(in srgb, var(--color-vultr-light-blue) 45%, transparent)"
          />
          <AppStoreProvider>
            <Toaster position="top-right" toastOptions={{ className: "rounded-[var(--radius-card)] shadow-[var(--shadow-soft)]" }} />
            <div className="relative flex min-h-screen flex-col bg-white dark:bg-vultr-midnight">
              <Nav />
              <main className="flex-1 overflow-x-hidden">{children}</main>
              <Footer />
            </div>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
