import type { Metadata } from "next";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { Toaster } from "sonner";
import { AppStoreProvider } from "@/stores/app-store";
import { ThemeProvider } from "@/components/theme-provider";

export const metadata: Metadata = {
  title: "Snappy! - Your Friendly Vision Retrieval Buddy",
  description: "Lightning-fast visual document search, upload, and conversational AI powered by ColPali",
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
          <AppStoreProvider>
            <Toaster position="top-right" />
            {/* 3-row viewport-aware layout with persistent footer */}
            <div className="flex h-full min-h-0 flex-col">
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
