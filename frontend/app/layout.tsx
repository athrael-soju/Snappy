import type { Metadata } from "next";
import "./globals.css";
import "@/lib/api/client";
import { Toaster } from "sonner";
import { AppStoreProvider } from "@/stores/app-store";
import { AppShell } from "@/components/layout/app-shell";

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
    <html lang="en">
      <body className="bg-background text-foreground antialiased">
        <AppStoreProvider>
          <Toaster position="top-right" />
          <AppShell>{children}</AppShell>
        </AppStoreProvider>
      </body>
    </html>
  );
}
