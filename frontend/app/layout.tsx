import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

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
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased relative h-screen flex flex-col overflow-hidden`}
      >
        {/* Site-wide background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-purple-50/30 to-cyan-50/50" />

        {/* Foreground content */}
        <div className="relative z-10 flex flex-col flex-1 min-h-0">
          <NextTopLoader showSpinner={false} />
          <Toaster richColors closeButton position="top-right" />
          <TooltipProvider>
            <Nav />
            <main className="flex-1 min-h-0 mx-auto max-w-6xl w-full p-4 sm:p-6 flex flex-col">
              {children}
            </main>
          </TooltipProvider>
        </div>
      </body>
    </html>
  );
}
