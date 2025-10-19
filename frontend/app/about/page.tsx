"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Braces,
  Database,
  Layers,
  Rocket,
  Scan,
  Server,
  Sparkles,
  Workflow,
} from "lucide-react";

import { AppButton } from "@/components/app-button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RoutePageShell } from "@/components/route-page-shell";

const highlights = [
  {
    title: "Vision-first retrieval",
    description:
      "Page renders become multivector embeddings via ColPali so search understands layout, charts, and visuals.",
    icon: Sparkles,
  },
  {
    title: "Batteries-included pipeline",
    description:
      "FastAPI orchestration, Qdrant storage, and MinIO image serving are pre-wired with Docker Compose.",
    icon: Workflow,
  },
  {
    title: "Modern operator experience",
    description:
      "Next.js 15 App Router UI ships upload progress, streaming chat, runtime configuration, and maintenance tools.",
    icon: Rocket,
  },
] as const;

const stack = [
  {
    title: "FastAPI backend",
    description:
      "Async routers handle indexing, retrieval, configuration edits, and system maintenance with SSE progress feeds.",
    icon: Server,
  },
  {
    title: "ColPali embeddings",
    description:
      "Dedicated service turns PDF pages into dense multivectors, preserving spatial cues for grounded answers.",
    icon: Scan,
  },
  {
    title: "Qdrant vector store",
    description:
      "Multivector collections power hybrid search, optional binary quantisation, and MUVERA first-stage retrieval.",
    icon: Database,
  },
  {
    title: "MinIO object storage",
    description:
      "Keeps page imagery in sync with vector IDs so chat and search can surface visual citations instantly.",
    icon: Layers,
  },
] as const;

const lifecycle = [
  {
    label: "Prepare",
    detail:
      "Drop PDFs or ingest via the API. Poppler renders pages server-side so vision models see the full layout.",
  },
  {
    label: "Index",
    detail:
      "The backend pipelines page renders through ColPali, uploads imagery to MinIO, and persists embeddings to Qdrant.",
  },
  {
    label: "Retrieve",
    detail:
      "Search requests fan out to Qdrant with configurable top-K, filters, and optional MUVERA recall boost.",
  },
  {
    label: "Respond",
    detail:
      "The edge chat route streams OpenAI Responses events alongside kb.images updates for visual grounding.",
  },
  {
    label: "Operate",
    detail:
      "Configuration and maintenance dashboards expose runtime tuning, resets, and system health at a glance.",
  },
] as const;

export default function AboutPage() {
  const heroActions = (
    <>
      <AppButton
        asChild
        variant="primary"
        size="sm"
        className="rounded-[var(--radius-button)] px-5"
      >
        <Link href="/chat">Explore chat demo</Link>
      </AppButton>
      <AppButton
        asChild
        variant="ghost"
        size="sm"
        className="rounded-[var(--radius-button)] border border-white/30 bg-white/10 px-4 py-2 text-white hover:border-white/50 hover:bg-white/20"
      >
        <Link href="/search">See search workflow</Link>
      </AppButton>
    </>
  );

  const heroMeta = (
    <>
      <span className="inline-flex items-center gap-1 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-body-sm font-medium text-white backdrop-blur">
        <Sparkles className="size-icon-3xs" />
        Vision-first retrieval
      </span>
      <span className="inline-flex items-center gap-1 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-body-sm font-medium text-white backdrop-blur">
        <Server className="size-icon-3xs" />
        FastAPI · Qdrant · MinIO stack
      </span>
      <span className="inline-flex items-center gap-1 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-body-sm font-medium text-white backdrop-blur">
        <Workflow className="size-icon-3xs" />
        End-to-end operations
      </span>
    </>
  );

  return (
    <RoutePageShell
      eyebrow="Platform"
      title="Vultr Vision brings ColPali intelligence to your cloud"
      description="The turnkey template blends Vultr’s brand system with ColPali’s document vision pipeline so teams can launch grounded search, chat, and maintenance in record time."
      actions={heroActions}
      meta={heroMeta}
    >
      <motion.div
        className="mx-auto flex w-full max-w-5xl flex-col gap-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <motion.section
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
        >
          {highlights.map((item, index) => (
            <motion.div
              key={item.title}
              className="flex flex-col gap-3 rounded-2xl border border-border/20 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-lg dark:border-white/15 dark:bg-vultr-midnight/60"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05, duration: 0.3 }}
            >
              <div className="flex size-icon-lg items-center justify-center rounded-full bg-primary/10 text-primary shadow-sm">
                <item.icon className="size-icon-sm" />
              </div>
              <div className="space-y-1">
                <h3 className="text-body font-semibold text-foreground">{item.title}</h3>
                <p className="text-body-xs text-muted-foreground leading-relaxed">{item.description}</p>
              </div>
            </motion.div>
          ))}
        </motion.section>

        <motion.section
          className="space-y-6"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.3 }}
        >
          <Card className="border border-border/20 bg-white shadow-sm dark:border-white/15 dark:bg-vultr-midnight/60">
            <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div className="space-y-2">
                <CardTitle className="text-digital-h4 font-semibold text-balance">Vultr Vision stack</CardTitle>
                <CardDescription className="max-w-3xl text-body-sm leading-relaxed">
                  Each service is optimised for fast setup on Vultr infrastructure. Customise connectors, GPU regions,
                  and storage policies without rebuilding the UI.
                </CardDescription>
              </div>
              <AppButton asChild variant="outline" size="sm" className="rounded-[var(--radius-button)]">
                <Link href="/configuration">Review configuration</Link>
              </AppButton>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {stack.map((item, index) => (
                <motion.div
                  key={item.title}
                  className="flex flex-col gap-3 rounded-2xl border border-border/20 bg-background/70 p-4 shadow-sm transition hover:border-primary/40 dark:border-white/15 dark:bg-vultr-midnight/50"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.05, duration: 0.25 }}
                >
                  <div className="flex size-icon-lg items-center justify-center rounded-full bg-primary/10 text-primary shadow-sm">
                    <item.icon className="size-icon-sm" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-body-sm font-semibold">{item.title}</h3>
                    <p className="text-body-xs text-muted-foreground leading-relaxed">{item.description}</p>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          <Card className="border border-border/20 bg-white shadow-sm dark:border-white/15 dark:bg-vultr-midnight/60">
            <CardHeader>
              <CardTitle className="text-digital-h5 font-semibold text-balance">Built for developers</CardTitle>
              <CardDescription className="text-body-sm leading-relaxed">
                OpenAPI powered SDKs, typed stores, and shadcn UI primitives keep the codebase approachable.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-body-sm text-muted-foreground">
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/70 p-3 dark:border-white/15 dark:bg-vultr-midnight/50 text-body-xs ">
                <Braces className="size-icon-xs text-primary" />
                <span>Generated TypeScript clients stay in sync with FastAPI routes.</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/70 p-3 dark:border-white/15 dark:bg-vultr-midnight/50 text-body-xs ">
                <Workflow className="size-icon-xs text-primary" />
                <span>Shared event bus keeps upload, search, and chat in lockstep.</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/70 p-3 dark:border-white/15 dark:bg-vultr-midnight/50 text-body-xs ">
                <Rocket className="size-icon-xs text-primary" />
                <span>Docker-first setup mirrors local testing and Vultr production.</span>
              </div>
            </CardContent>
          </Card>
        </motion.section>

        <motion.section
          className="rounded-3xl border border-border/20 bg-white p-8 shadow-sm dark:border-white/15 dark:bg-vultr-midnight/60"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.35 }}
        >
          <div className="mx-auto max-w-4xl space-y-6 text-center">
            <h2 className="text-editorial-h3 font-semibold">From PDF to grounded answer</h2>
            <p className="text-body-sm text-muted-foreground sm:text-body">
              The end-to-end workflow keeps context intact, from ingestion through search and response streaming.
            </p>
          </div>
          <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {lifecycle.map((item, index) => (
              <motion.li
                key={item.label}
                className="relative flex h-full flex-col gap-3 rounded-2xl border border-border/20 bg-background/70 p-5 text-left shadow-sm transition hover:-translate-y-1 hover:border-primary/40 dark:border-white/15 dark:bg-vultr-midnight/50"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35 + index * 0.05, duration: 0.3 }}
              >
                <span className="flex size-icon-2xl items-center justify-center rounded-full border border-border/20 bg-muted/70 text-body-sm font-semibold text-muted-foreground shadow-sm dark:border-white/15 dark:bg-vultr-midnight/70">
                  {index + 1}
                </span>
                <h3 className="text-body-sm sm:text-body font-semibold">{item.label}</h3>
                <p className="text-body-xs text-muted-foreground leading-relaxed">{item.detail}</p>
              </motion.li>
            ))}
          </ol>
        </motion.section>

        <motion.section
          className="rounded-3xl border border-primary/30 bg-gradient-to-br from-primary/10 via-white to-chart-4/10 p-8 text-center shadow-sm dark:border-vultr-light-blue/30 dark:from-vultr-blue-20/40 dark:via-vultr-midnight dark:to-vultr-blue-20/50 lg:p-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.35 }}
        >
          <h2 className="text-editorial-h3 font-semibold">Ready to tailor it to your domain?</h2>
          <p className="mt-3 text-body-sm text-muted-foreground sm:text-body">
            Bring your PDFs, plug in your ColPali deployment, and start experimenting. Feature flags cover MUVERA
            recall boosts, binary quantisation, and runtime configuration so you can harden as you grow.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
            <AppButton asChild size="lg" variant="cta" elevated iconShift>
              <Link href="/chat">
                Try grounded chat
                <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
              </Link>
            </AppButton>
            <AppButton asChild size="lg" variant="outline" elevated iconShift>
              <Link href="/maintenance">
                View maintenance tools
                <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
              </Link>
            </AppButton>
          </div>
        </motion.section>
      </motion.div>
    </RoutePageShell>
  );
}

