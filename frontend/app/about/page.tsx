"use client"

import Link from "next/link"
import { motion } from "framer-motion"
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
} from "lucide-react"
import { AppButton } from "@/components/app-button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { PageHeader } from "@/components/page-header"

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
]

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
]

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
]

export default function AboutPage() {
  return (
    <div className="relative flex min-h-full flex-col overflow-x-hidden">
      <section className="px-4 py-10 sm:px-6 lg:px-8">
        <motion.div
          className="mx-auto flex w-full max-w-5xl flex-col gap-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <motion.header
            className="shrink-0"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
          >
            <PageHeader
              align="center"
              spacing="lg"
              title={
                <>
                  <span className="bg-gradient-to-r from-vultr-sky-blue via-white to-vultr-blue bg-clip-text text-transparent">
                    Vultr Vision
                  </span>{" "}
                  brings ColPali intelligence to your cloud
                </>
              }
              description="This Vultr-branded workspace aligns FastAPI, Next.js, ColPali, Qdrant, and MinIO so you can deploy a production-ready vision retrieval stack without rebuilding the plumbing. Upload documents, search visually, and chat with grounded citations out of the box."
              descriptionClassName="text-body-sm sm:text-body leading-relaxed text-muted-foreground max-w-3xl"
              actionsClassName="gap-4 flex-wrap justify-center"
              actions={
                <>
                  <AppButton
                    asChild
                    variant="hero"
                    size="xl"
                    elevated
                    iconShift
                  >
                    <Link href="/upload">
                      Start indexing
                      <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
                    </Link>
                  </AppButton>
                  <AppButton
                    asChild
                    variant="glass"
                    size="xl"
                    elevated
                    iconShift
                  >
                    <Link href="/search">
                      Explore search
                      <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
                    </Link>
                  </AppButton>
                </>
              }
            />
          </motion.header>

          <section className="grid gap-4 md:grid-cols-3">
            {highlights.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.1, duration: 0.4 }}
                whileHover={{ scale: 1.03, y: -4 }}
                whileTap={{ scale: 0.98 }}
              >
                <Card className="border-border/50 bg-card/60 backdrop-blur transition hover:border-primary/50 hover:shadow-lg hover:shadow-primary/15 touch-manipulation">
                  <CardHeader className="gap-4">
                    <div className="flex size-icon-3xl items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-chart-4/20 text-primary shadow-md">
                      <item.icon className="size-icon-lg" />
                    </div>
                    <CardTitle className="text-body sm:text-lg">{item.title}</CardTitle>
                    <CardDescription className="text-body-sm sm:text-body leading-relaxed">
                      {item.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </motion.div>
            ))}
          </section>

          <motion.section
            className="grid gap-6 lg:grid-cols-3"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <Card className="lg:col-span-2 border-border/60 bg-card/70 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-2xl font-semibold">How the pieces fit together</CardTitle>
                <CardDescription className="text-body-sm leading-relaxed">
                  Each service is container-ready and connected with sensible defaults so you can deploy locally or
                  scale into production with minimal wiring.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="grid gap-4 sm:grid-cols-2">
                  {stack.map((item, index) => (
                    <motion.li
                      key={item.title}
                      className="flex gap-3 rounded-xl border border-border/40 bg-background/60 p-4 transition hover:border-primary/40 touch-manipulation"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.6 + index * 0.1, duration: 0.3 }}
                      whileHover={{ scale: 1.02, x: 4 }}
                    >
                      <div className="mt-1 flex size-icon-2xl items-center justify-center rounded-lg bg-primary/10 text-primary shadow-sm">
                        <item.icon className="size-icon-md" />
                      </div>
                      <div className="space-y-1.5">
                        <p className="text-body-sm sm:text-body font-semibold">{item.title}</p>
                        <p className="text-body-xs sm:text-body-sm text-muted-foreground leading-relaxed">
                          {item.description}
                        </p>
                      </div>
                    </motion.li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="border-border/60 bg-card/70 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-xl font-semibold">Built for developers</CardTitle>
                <CardDescription className="text-body-sm leading-relaxed">
                  OpenAPI powered SDKs, typed stores, and shadcn UI primitives keep the codebase approachable.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-body-sm text-muted-foreground">
                <div className="flex items-center gap-2 rounded-lg border border-border/40 bg-background/60 p-3">
                  <Braces className="size-icon-xs text-primary" />
                  <span>Generated TypeScript clients sync with FastAPI routes.</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-border/40 bg-background/60 p-3">
                  <Workflow className="size-icon-xs text-primary" />
                  <span>Shared event bus keeps upload, search, and chat in sync.</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-border/40 bg-background/60 p-3">
                  <Rocket className="size-icon-xs text-primary" />
                  <span>Docker-first setup mirrors local and production environments.</span>
                </div>
              </CardContent>
            </Card>
          </motion.section>

          <motion.section
            className="rounded-3xl border border-border/40 bg-muted/30 p-6 backdrop-blur lg:p-10"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7, duration: 0.5 }}
          >
            <div className="mx-auto max-w-4xl space-y-6 text-center">
              <h2 className="text-2xl font-semibold sm:text-3xl">From PDF to grounded answer</h2>
              <p className="text-body-sm text-muted-foreground sm:text-body">
                The end-to-end workflow keeps context intact, from ingestion all the way to answer streaming.
              </p>
            </div>
            <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
              {lifecycle.map((item, index) => (
                <motion.li
                  key={item.label}
                  className="relative flex h-full flex-col gap-3 rounded-2xl border border-border/30 bg-background/60 p-5 text-left transition-all hover:border-primary/40 hover:shadow-md touch-manipulation"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 + index * 0.1, duration: 0.3 }}
                  whileHover={{ scale: 1.05, y: -5 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="flex size-icon-2xl items-center justify-center rounded-full border border-border/40 bg-muted/70 text-body-sm font-semibold text-muted-foreground shadow-sm">
                    {index + 1}
                  </span>
                  <h3 className="text-body-sm sm:text-body font-semibold">{item.label}</h3>
                  <p className="text-body-xs sm:text-body-sm text-muted-foreground leading-relaxed">{item.detail}</p>
                </motion.li>
              ))}
            </ol>
          </motion.section>

          <motion.section
            className="rounded-3xl border border-primary/30 bg-gradient-to-br from-primary/10 via-background to-chart-4/10 p-6 text-center backdrop-blur lg:p-10"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.5 }}
          >
            <h2 className="text-2xl font-semibold sm:text-3xl">Ready to tailor it to your domain?</h2>
            <p className="mt-3 text-body-sm text-muted-foreground sm:text-body">
              Bring your PDFs, plug in your ColPali deployment, and start experimenting. The template includes
              feature flags for MUVERA recall boosts, binary quantisation, and runtime configuration so you can
              harden as you grow.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
              <AppButton
                asChild
                size="lg"
                variant="hero"
                elevated
                iconShift
              >
                <Link href="/chat">
                  Try grounded chat
                  <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
                </Link>
              </AppButton>
              <AppButton
                asChild
                size="lg"
                variant="glass"
                elevated
                iconShift
              >
                <Link href="/maintenance">
                  View maintenance tools
                  <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
                </Link>
              </AppButton>
            </div>
          </motion.section>
        </motion.div>
      </section>
    </div>
  )
}
