"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  defaultPageMotion,
  fadeInItemMotion,
  sectionVariants,
  staggeredListMotion,
} from "@/lib/motion-presets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  CloudUpload,
  Eye,
  MessageCircle,
  Sparkles,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const featureCards = [
  {
    title: "Upload without friction",
    description:
      "Drop PDFs or images and Snappy handles page conversion, status updates, and storage so you can stay in flow.",
    icon: CloudUpload,
    href: "/upload",
  },
  {
    title: "Search what you can see",
    description:
      "Visual-first retrieval keeps layout and imagery intact with ColPali embeddings packed into Qdrant multivectors.",
    icon: Eye,
    href: "/search",
  },
  {
    title: "Chat with receipts",
    description:
      "AI answers arrive with precise visual citations and shareable links so teams can trust every response.",
    icon: MessageCircle,
    href: "/chat",
  },
] as const;

const stackHighlights = [
  {
    title: "Visual-first retrieval",
    description:
      "ColPali embeddings capture layout context so answers reference the exact page patches people care about.",
  },
  {
    title: "Friendly ingestion pipeline",
    description:
      "FastAPI streams ingestion progress, keeps MinIO and Qdrant in sync, and lets you monitor everything from one panel.",
  },
  {
    title: "Ready-to-ship UI",
    description:
      "Next.js 15, reusable stores, and polished components mean you can polish experience instead of wiring boilerplate.",
  },
] as const;

export default function Home() {
  return (
    <motion.div {...defaultPageMotion} className="page-shell flex min-h-0 flex-1 flex-col">
      <motion.section
        variants={sectionVariants}
        className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-4 pb-12 pt-10 sm:pt-14 lg:flex-row lg:items-center"
      >
        <div className="flex flex-1 flex-col gap-6">
          <Badge
            variant="outline"
            className="w-fit rounded-full border-primary/30 bg-primary/10 px-3 py-1 text-sm font-semibold text-primary"
          >
            Meet Snappy v0.1
          </Badge>
          <h1 className="text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Build visual document answers your team can trust.
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground">
            Snappy bundles FastAPI, Next.js, Qdrant, and a ColPali-powered embedding
            service into a calm starter so you can focus on the experience you&apos;re
            delivering—not the plumbing.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Button
              asChild
              size="lg"
              className="rounded-xl px-6 py-6 text-base font-semibold shadow-sm"
            >
              <Link href="/upload">
                <CloudUpload className="mr-2 h-5 w-5" />
                Upload a file
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="rounded-xl px-6 py-6 text-base"
            >
              <Link href="/search">Explore search</Link>
            </Button>
          </div>
          <div className="flex flex-col gap-3 text-sm text-muted-foreground sm:flex-row sm:items-center sm:gap-5">
            <span className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Visual-first RAG in a single starter
            </span>
            <span className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Batteries-included maintenance dashboard
            </span>
          </div>
        </div>

        <div className="flex flex-1 justify-center lg:justify-end">
          <div className="relative flex h-64 w-64 items-center justify-center sm:h-72 sm:w-72">
            <div className="absolute inset-0 rounded-full bg-primary/10 blur-3xl" aria-hidden />
            <div className="absolute -inset-3 rounded-[32px] border border-primary/20 bg-card/70 shadow-lg backdrop-blur">
              <div className="relative h-full w-full overflow-hidden rounded-[28px] p-6">
                <Image
                  src="/Snappy/snappy_light_nobg_resized.png"
                  alt="Snappy the mascot"
                  fill
                  sizes="(min-width: 1024px) 18rem, 16rem"
                  className="object-contain dark:hidden"
                  priority
                />
                <Image
                  src="/Snappy/snappy_dark_nobg_resized.png"
                  alt="Snappy the mascot"
                  fill
                  sizes="(min-width: 1024px) 18rem, 16rem"
                  className="hidden object-contain dark:block"
                  priority
                />
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section
        variants={sectionVariants}
        className="flex-1 min-h-0 bg-muted/30 py-10 sm:py-12"
      >
        <div className="mx-auto flex h-full w-full max-w-6xl flex-col gap-8 px-4">
          <motion.div
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            {...staggeredListMotion}
          >
            {featureCards.map(({ title, description, icon: Icon, href }) => (
              <motion.div key={title} {...fadeInItemMotion}>
                <Link href={href}>
                  <Card className="h-full border-border/60 transition-colors hover:border-primary/40">
                    <CardHeader className="flex flex-col gap-4">
                      <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Icon className="h-5 w-5" />
                      </span>
                      <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm leading-relaxed text-muted-foreground">
                        {description}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </motion.div>

          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="text-xl font-semibold">The Snappy stack</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
              <ul className="space-y-3">
                {stackHighlights.map(({ title, description }) => (
                  <li key={title} className="space-y-1.5">
                    <span className="font-semibold text-foreground">{title}</span>
                    <p>{description}</p>
                  </li>
                ))}
              </ul>
              <div className="pt-2">
                <Link
                  href="/about"
                  className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:text-primary/80"
                >
                  Discover how Snappy works
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.section>
    </motion.div>
  );
}
