import type { Metadata } from "next";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { Toaster } from "sonner";
import { AppStoreProvider } from "@/stores/app-store";
import { ThemeProvider } from "@/components/theme-provider";
import { ScrollArea } from "@/components/ui/scroll-area";

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
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans bg-background text-foreground antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AppStoreProvider>
            <Toaster position="top-right" />
            {/* 3-row viewport-constrained layout */}
            <div className="flex h-dvh flex-col overflow-hidden">
              {/* Row 1: Fixed Header */}
              <Nav />
              
              {/* Row 2: Scrollable Content */}
              <ScrollArea className="flex-1">
                {children}
              </ScrollArea>
              
              {/* Row 3: Fixed Footer */}
              <Footer />
            </div>
          </AppStoreProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
