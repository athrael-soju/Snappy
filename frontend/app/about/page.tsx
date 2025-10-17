import Link from "next/link"
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
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

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
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-10">
          <header className="space-y-6 text-center">
            <div className="space-y-4">
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
                <span className="bg-gradient-to-r from-primary via-chart-4 to-chart-1 bg-clip-text text-transparent">
                  Snappy!
                </span>{" "}
                is your launchpad for multimodal retrieval
              </h1>
              <p className="mx-auto max-w-3xl text-sm leading-relaxed text-muted-foreground">
                This template stitches together FastAPI, Next.js, ColPali, Qdrant, and MinIO so you can stand up
                a production-ready vision retrieval stack without rebuilding the plumbing. Upload documents,
                search visually, and chat with grounded citations out of the box.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Button
                asChild
                size="lg"
                className="group h-12 gap-2 rounded-full px-6 text-base shadow-lg shadow-primary/25"
              >
                <Link href="/upload">
                  Start indexing
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-12 gap-2 rounded-full border-2 bg-background/60 px-6 text-base backdrop-blur"
              >
                <Link href="/search">
                  Explore search
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
            </div>
          </header>

          <section className="grid gap-4 md:grid-cols-3">
            {highlights.map((item) => (
              <Card
                key={item.title}
                className="border-border/50 bg-card/60 backdrop-blur transition hover:border-primary/50 hover:shadow-lg hover:shadow-primary/15"
              >
                <CardHeader className="gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-chart-4/20 text-primary">
                    <item.icon className="h-6 w-6" />
                  </div>
                  <CardTitle className="text-lg">{item.title}</CardTitle>
                  <CardDescription className="text-sm leading-relaxed">
                    {item.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2 border-border/60 bg-card/70 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-2xl font-semibold">How the pieces fit together</CardTitle>
                <CardDescription className="text-sm leading-relaxed">
                  Each service is container-ready and connected with sensible defaults so you can deploy locally or
                  scale into production with minimal wiring.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="grid gap-4 sm:grid-cols-2">
                  {stack.map((item) => (
                    <li
                      key={item.title}
                      className="flex gap-3 rounded-xl border border-border/40 bg-background/60 p-4 transition hover:border-primary/40"
                    >
                      <div className="mt-1 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <item.icon className="h-5 w-5" />
                      </div>
                      <div className="space-y-1.5">
                        <p className="text-sm font-semibold">{item.title}</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {item.description}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="border-border/60 bg-card/70 backdrop-blur">
              <CardHeader>
                <CardTitle className="text-xl font-semibold">Built for developers</CardTitle>
                <CardDescription className="text-sm leading-relaxed">
                  OpenAPI powered SDKs, typed stores, and shadcn UI primitives keep the codebase approachable.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2 rounded-lg border border-border/40 bg-background/60 p-3">
                  <Braces className="h-4 w-4 text-primary" />
                  <span>Generated TypeScript clients sync with FastAPI routes.</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-border/40 bg-background/60 p-3">
                  <Workflow className="h-4 w-4 text-primary" />
                  <span>Shared event bus keeps upload, search, and chat in sync.</span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-border/40 bg-background/60 p-3">
                  <Rocket className="h-4 w-4 text-primary" />
                  <span>Docker-first setup mirrors local and production environments.</span>
                </div>
              </CardContent>
            </Card>
          </section>

          <section className="rounded-3xl border border-border/40 bg-muted/30 p-6 backdrop-blur lg:p-10">
            <div className="mx-auto max-w-4xl space-y-6 text-center">
              <h2 className="text-2xl font-semibold sm:text-3xl">From PDF to grounded answer</h2>
              <p className="text-sm text-muted-foreground sm:text-base">
                The end-to-end workflow keeps context intact, from ingestion all the way to answer streaming.
              </p>
            </div>
            <ol className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
              {lifecycle.map((item, index) => (
                <li
                  key={item.label}
                  className="relative flex h-full flex-col gap-3 rounded-2xl border border-border/30 bg-background/60 p-5 text-left"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {index + 1}
                  </span>
                  <h3 className="text-base font-semibold">{item.label}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{item.detail}</p>
                </li>
              ))}
            </ol>
          </section>

          <section className="rounded-3xl border border-primary/30 bg-gradient-to-br from-primary/10 via-background to-chart-4/10 p-6 text-center backdrop-blur lg:p-10">
            <h2 className="text-2xl font-semibold sm:text-3xl">Ready to tailor it to your domain?</h2>
            <p className="mt-3 text-sm text-muted-foreground sm:text-base">
              Bring your PDFs, plug in your ColPali deployment, and start experimenting. The template includes
              feature flags for MUVERA recall boosts, binary quantisation, and runtime configuration so you can
              harden as you grow.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
              <Button
                asChild
                size="lg"
                className="h-12 gap-2 rounded-full px-6 text-base shadow-lg shadow-primary/20"
              >
                <Link href="/chat">
                  Try grounded chat
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-12 gap-2 rounded-full border-2 bg-background/50 px-6 text-base backdrop-blur"
              >
                <Link href="/maintenance">
                  View maintenance tools
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
            </div>
          </section>
        </div>
      </section>
    </div>
  )
}
