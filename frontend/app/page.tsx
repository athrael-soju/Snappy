"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Upload,
  Search as SearchIcon,
  MessageSquare,
  Sparkles,
  Layers,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

const heroMotion = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.45, ease: "easeOut" },
};

const sectionMotion = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.35, ease: "easeOut" },
};

const cardMotion = {
  initial: { opacity: 0, y: 12 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.3 },
};

const featureCards = [
  {
    title: "Bring visuals online",
    description:
      "Drop PDFs or image heavy reports from desktop or phone. Snappy slices and stores every page automatically.",
    icon: Upload,
    href: "/upload",
    cta: "Upload files",
  },
  {
    title: "Search what you see",
    description:
      "Combine text queries with layout awareness so charts, forms, and tables stay in context on any screen.",
    icon: SearchIcon,
    href: "/search",
    cta: "Open search",
  },
  {
    title: "Chat with screenshots",
    description:
      "Ask questions that reference visual snippets. Citations stay tappable even on narrow viewports.",
    icon: MessageSquare,
    href: "/chat",
    cta: "Start chatting",
  },
] as const;

const quickStartSteps = [
  {
    label: "Upload",
    description: "Drag and drop or browse for files. Progress indicators adapt to narrow layouts.",
    icon: Upload,
  },
  {
    label: "Search",
    description: "Use natural language or presets. Controls stack vertically when space is limited.",
    icon: SearchIcon,
  },
  {
    label: "Chat",
    description: "Review answers with image citations that open in a full width lightbox.",
    icon: MessageSquare,
  },
] as const;

const experienceHighlights = [
  {
    icon: Sparkles,
    title: "Thumb friendly controls",
    description: "Primary actions expand to full width on small screens so they stay easy to reach.",
  },
  {
    icon: Layers,
    title: "Adaptive layout system",
    description:
      "Forms and cards flow into single column stacks on phones, then scale into multi column grids on larger displays.",
  },
] as const;

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-10 px-4 py-8 sm:px-6 lg:px-8">
      <motion.section
        {...heroMotion}
        className="overflow-hidden rounded-3xl border bg-gradient-to-br from-primary/5 via-background to-background p-6 sm:p-10"
      >
        <div className="flex flex-col gap-6">
          <Badge className="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            Template: FastAPI + Next.js
          </Badge>
          <div className="space-y-4">
            <h1 className="text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-5xl sm:leading-tight">
              Build visual retrieval that feels great on mobile.
            </h1>
            <p className="text-pretty text-sm text-muted-foreground sm:text-lg">
              Snappy pairs a FastAPI backend with a responsive shadcn powered Next.js UI. Every workflow has been tuned
              to collapse gracefully on phones and stretch comfortably on larger viewports.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
            <Button asChild size="lg" className="w-full sm:w-auto">
              <Link href="/upload">
                Ingest a document
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
              <Link href="/search">Try the search workflow</Link>
            </Button>
          </div>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} className="grid gap-4 md:grid-cols-2">
        <Card className="h-full">
          <CardHeader className="space-y-2">
            <CardTitle className="text-lg font-semibold">Three step setup</CardTitle>
            <CardDescription>Stay productive on desktop or mobile with the same flows.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <ol className="space-y-3 text-sm text-muted-foreground">
              {quickStartSteps.map(({ label, description, icon: Icon }) => (
                <li key={label} className="flex items-start gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Icon className="h-4 w-4" />
                  </span>
                  <div className="space-y-1">
                    <p className="font-semibold text-foreground">{label}</p>
                    <p>{description}</p>
                  </div>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader className="space-y-2">
            <CardTitle className="text-lg font-semibold">Responsive by default</CardTitle>
            <CardDescription>Built with Tailwind v4 utilities and shadcn components.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            {experienceHighlights.map(({ icon: Icon, title, description }) => (
              <div key={title} className="flex items-start gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
                  <Icon className="h-4 w-4" />
                </span>
                <div className="space-y-1">
                  <p className="font-semibold text-foreground">{title}</p>
                  <p>{description}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ ...sectionMotion.transition, delay: 0.05 }} className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-foreground sm:text-2xl">Core workflows</h2>
          <p className="text-sm text-muted-foreground sm:text-base">
            Jump straight into ingestion, retrieval, and chat. Cards scroll horizontally on mobile and fall into a grid
            on larger screens.
          </p>
        </div>

        <div className="-mx-4 sm:hidden">
          <ScrollArea className="w-[calc(100%+2rem)] px-4 pb-2">
            <div className="flex w-max gap-4">
              {featureCards.map((feature) => (
                <motion.div
                  key={feature.title}
                  {...cardMotion}
                  className="w-[min(18.75rem,calc(100vw-4rem))] shrink-0"
                >
                  <FeatureCardItem feature={feature} />
                </motion.div>
              ))}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </div>

        <div className="hidden sm:grid sm:grid-cols-2 lg:grid-cols-3 sm:gap-4 lg:gap-6">
          {featureCards.map((feature) => (
            <motion.div key={feature.title} {...cardMotion}>
              <FeatureCardItem feature={feature} />
            </motion.div>
          ))}
        </div>
      </motion.section>
    </div>
  );
}

function FeatureCardItem({
  feature,
}: {
  feature: (typeof featureCards)[number];
}) {
  const { title, description, icon: Icon, href, cta } = feature;

  return (
    <Card className="flex h-full flex-col border-muted">
      <CardHeader className="space-y-3">
        <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-4 text-sm text-muted-foreground">
        <p>{description}</p>
        <Button
          asChild
          variant="ghost"
          className="mt-auto justify-start gap-2 px-0 text-sm font-semibold sm:w-fit"
        >
          <Link href={href}>
            {cta}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
