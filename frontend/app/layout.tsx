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
  title: "Snappy! - Vision-First Document Intelligence",
  description: "Lightning-fast visual document search, intelligent chat, and seamless upload powered by ColPali AI",
  icons: {
    icon: "/Snappy/snappy_light_nobg_resized.png",
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
      <body className="h-dvh overflow-hidden bg-background font-sans text-foreground antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <NextTopLoader
            color="linear-gradient(90deg, hsl(var(--chart-1)), hsl(var(--chart-2)), hsl(var(--chart-4)))"
            initialPosition={0.08}
            crawlSpeed={200}
            height={3}
            crawl={true}
            showSpinner={false}
            easing="ease"
            speed={200}
            shadow="0 0 10px hsl(var(--chart-1)),0 0 5px hsl(var(--chart-2))"
          />
          <AppStoreProvider>
            <Toaster position="top-right" />
            {/* 3-row viewport-aware layout with persistent footer */}
            <div className="relative flex h-full min-h-0 flex-col">
              {/* Animated gradient background */}
              <div className="pointer-events-none fixed inset-0 -z-10">
                <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted/30" />
                <div className="absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-primary/8 via-primary/3 to-transparent" />
                <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-primary/15 blur-3xl dark:bg-primary/8" />
                <div className="absolute top-1/3 -right-24 h-96 w-96 rounded-full bg-accent/15 blur-3xl dark:bg-accent/8" />
                <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-secondary/15 blur-3xl dark:bg-secondary/8" />
              </div>

              {/* Row 1: Fixed Header */}
              <Nav />
              {/* Row 2: Component-controlled scroll area */}
              <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
                {children}
              </main>
              {/* Row 3: Persistent Footer */}
              <Footer />
            </div>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
