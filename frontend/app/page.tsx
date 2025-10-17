"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Upload,
  Search,
  MessageSquare,
  Settings,
  Wrench,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const primaryFeatures = [
  {
    title: "Upload & Index",
    description: "Drop documents and let Snappy's ColPali vision model understand layout and content instantly.",
    href: "/upload",
    icon: Upload,
    gradient: "from-chart-1 to-chart-2",
  },
  {
    title: "Search Naturally",
    description: "Ask questions in plain language and Snappy surfaces precise, citation-ready answers.",
    href: "/search",
    icon: Search,
    gradient: "from-primary to-chart-4",
  },
  {
    title: "Chat & Discover",
    description: "Have conversations with your documents powered by Snappy's visual reasoning.",
    href: "/chat",
    icon: MessageSquare,
    gradient: "from-chart-2 to-chart-3",
  },
];

const secondaryLinks = [
  { title: "Configuration", href: "/configuration", icon: Settings },
  { title: "Maintenance", href: "/maintenance", icon: Wrench },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 100, damping: 10 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 100, damping: 15 },
  },
};

export default function Home() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const logoSrc =
    theme === "dark"
      ? "/Snappy/snappy_dark_nobg_resized.png"
      : "/Snappy/snappy_light_nobg_resized.png";

  return (
    <div className="relative flex min-h-0 flex-1 flex-col justify-between overflow-y-auto">
      {/* Hero Content - Full viewport utilization */}
      <motion.div
        className="flex flex-1 flex-col justify-center px-4 py-4 text-center sm:px-6 lg:px-8"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        <div className="mx-auto w-full max-w-6xl space-y-8">

          {/* Brandmark */}
          <motion.div variants={itemVariants}>
            <div className="relative mx-auto flex hero-logo-frame items-center justify-center sm:hero-logo-frame-lg">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 rounded-full bg-gradient-to-br from-primary/30 via-primary/15 to-transparent opacity-90 blur-2xl hero-logo-radiance"
              />
              {mounted && (
                <Image
                  src={logoSrc}
                  alt="Snappy logo"
                  width={270}
                  height={270}
                  priority
                  className="relative hero-logo-image object-contain drop-shadow-2xl sm:hero-logo-image-lg"
                />
              )}
            </div>
            {/* Heading */}
            <motion.h1
              className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl"
              variants={itemVariants}
            >
              <span className="bg-gradient-to-r from-primary via-chart-4 to-chart-1 bg-clip-text text-transparent">
                Your Vision Retrieval Buddy!
              </span>
            </motion.h1>
          </motion.div>



          {/* Description */}
          <motion.p
            className="mx-auto max-w-2xl text-body text-muted-foreground"
            variants={itemVariants}
          >
            Snappy combines lightning-fast ingestion with context-aware retrieval so your team can move
            from document to decision in seconds.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="flex flex-wrap items-center justify-center gap-3 sm:gap-4"
            variants={itemVariants}
          >
            <Button
              asChild
              size="lg"
              className="group h-12 gap-2 rounded-full px-6 hero-cta-text shadow-lg shadow-primary/20 transition-all hover:-translate-y-0.5 hover:shadow-2xl hover:shadow-primary/40 touch-manipulation"
            >
              <Link href="/upload">
                <Upload className="size-icon-md" />
                Get Started
                <ArrowRight className="size-icon-2xs transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-12 gap-2 rounded-full border-2 bg-background/50 px-6 text-body backdrop-blur-sm transition-all hover:bg-background touch-manipulation"
            >
              <Link href="/chat">
                <MessageSquare className="size-icon-md" />
                Try Chat
              </Link>
            </Button>
          </motion.div>

          {/* Core Features Section */}
          <motion.div className="pt-2" variants={itemVariants}>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-muted px-4 py-1.5 text-body font-medium">
              <Zap className="size-icon-sm text-primary" />
              Core Features
            </div>

            {/* Feature Cards */}
            <motion.div className="grid gap-4 md:grid-cols-3" variants={containerVariants}>
              {primaryFeatures.map((feature) => (
                <motion.div
                  key={feature.href}
                  variants={cardVariants}
                  whileHover={{ scale: 1.02, y: -4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Link
                    href={feature.href}
                    className="group relative block overflow-hidden rounded-2xl border border-border/50 bg-card/50 p-5 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-xl hover:shadow-primary/10 touch-manipulation"
                  >
                    <div
                      className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 transition-opacity group-hover:opacity-5`}
                    />

                    <div className="relative flex items-start gap-3">
                      <div
                        className={`flex size-icon-3xl shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${feature.gradient} shadow-lg`}
                      >
                        <feature.icon className="size-icon-lg text-primary-foreground" />
                      </div>

                      <div className="flex-1 text-left">
                        <h3 className="mb-1.5 text-lg font-bold">{feature.title}</h3>
                        <p className="mb-2 text-body-sm text-muted-foreground">
                          {feature.description}
                        </p>
                        <div className="inline-flex items-center gap-1.5 text-body-sm font-semibold text-primary">
                          Explore
                          <ArrowRight className="size-icon-2xs transition-transform group-hover:translate-x-2" />
                        </div>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </motion.div>

            {/* Secondary Links */}
            <motion.div
              className="mt-6 flex flex-wrap items-center justify-center gap-3"
              variants={itemVariants}
            >
              {secondaryLinks.map((link) => (
                <Button
                  key={link.href}
                  asChild
                  variant="ghost"
                  size="default"
                  className="gap-2 rounded-full px-4 text-body-sm"
                >
                  <Link href={link.href}>
                    <link.icon className="size-icon-2xs" />
                    {link.title}
                  </Link>
                </Button>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
