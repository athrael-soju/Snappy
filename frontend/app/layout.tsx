import type { Metadata } from "next";
import { Geist, Geist_Mono, Pixelify_Sans } from "next/font/google";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/8bit/tooltip";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Retro pixel font for 8bit UI
const pixel = Pixelify_Sans({
  variable: "--font-retro",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
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
        className={`${geistSans.variable} ${geistMono.variable} ${pixel.variable} antialiased relative h-screen flex flex-col overflow-hidden text-[15px] sm:text-base`}
      >
        {/* Pre-paint theme setter to prevent FOUC */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
            (function(){
              try {
                const ls = localStorage.getItem('theme');
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                const shouldDark = ls ? ls === 'dark' : prefersDark;
                const root = document.documentElement;
                if (shouldDark) root.classList.add('dark'); else root.classList.remove('dark');
              } catch (e) {}
            })();
          `,
          }}
        />
        {/* Site-wide background gradient using theme variables */}
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--color-card)] via-[var(--color-background)] to-[var(--color-card)]" />

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
