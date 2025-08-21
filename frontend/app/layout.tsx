import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@/lib/api/client";
import { Nav } from "@/components/nav";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Vision RAG UI",
  description: "Search, upload and chat with your visual documents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <NextTopLoader showSpinner={false} />
        <Toaster richColors closeButton position="top-right" />
        <Nav />
        <main className="mx-auto max-w-6xl p-4 sm:p-6">
          {children}
        </main>
      </body>
    </html>
  );
}
