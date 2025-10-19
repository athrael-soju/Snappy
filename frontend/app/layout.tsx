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
    "Deploy Vultr’s ColPali-powered document intelligence across your global infrastructure. Upload, search, and collaborate with Vultr’s signature performance.",
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
          href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,300;0,400;0,700;1,300;1,400;1,700&display=swap"
        />
      </head>
      <body className="h-dvh overflow-hidden font-sans antialiased">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <NextTopLoader
            color="#007bfc"
            initialPosition={0.12}
            crawlSpeed={250}
            height={3}
            crawl
            showSpinner={false}
            easing="ease"
            speed={240}
            shadow="0 0 18px rgba(0, 123, 252, 0.45)"
          />
          <AppStoreProvider>
            <Toaster position="top-right" toastOptions={{ className: "rounded-[var(--radius-card)] shadow-[var(--shadow-soft)]" }} />
            <div className="relative flex h-full min-h-0 flex-col">
              <div className="pointer-events-none fixed inset-0 -z-10">
                <div className="bg-hero-vultr absolute inset-x-0 top-0 h-[55%]" />
                <div className="absolute inset-0 bg-gradient-to-b from-vultr-blue/10 via-transparent to-warm-1" />
                <div className="absolute left-1/2 top-1/3 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-vultr-light-blue/35 blur-[140px]" />
                <div className="absolute bottom-[-10%] right-[12%] h-[320px] w-[320px] rounded-full bg-vultr-sky-blue/40 blur-[160px]" />
              </div>

              <Nav />
              <main className="flex min-h-0 flex-1 flex-col overflow-hidden">{children}</main>
              <Footer />
            </div>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
