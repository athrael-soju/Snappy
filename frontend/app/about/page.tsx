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
import { MortyMetaCard } from "@/components/morty-meta-card";

const highlights = [
  {
    title: "Morty's Visual Intelligence",
    description:
      "Morty sees your documents like you do - understanding charts, layouts, and visuals through advanced ColPali vision models.",
    icon: Sparkles,
  },
  {
    title: "Your Friendly Guide",
    description:
      "More than AI, Morty is your companion who makes complex document intelligence accessible and intuitive for everyone.",
    icon: Workflow,
  },
  {
    title: "Powered by Vultr",
    description:
      "Morty leverages Vultr's global GPU infrastructure and modern tech stack to deliver lightning-fast visual search and chat.",
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
  const heroMeta = (
    <MortyMetaCard
      label="Morty's visual intelligence lab"
      title="Engineer Morty calibrates Vultr infrastructure with ColPali models so vision search stays fast and friendly."
      bullets={[
        {
          icon: Sparkles,
          text: "Understands complex layouts, charts, and imagery like a human analyst.",
        },
        {
          icon: Workflow,
          text: "Keeps ingestion, retrieval, and chat pipelines synchronized across services.",
        },
        {
          icon: Rocket,
          text: "Taps Vultr's global GPU network to deliver lightning-fast responses.",
        },
      ]}
      image={{
        src: "/vultr/morty/engi_morty_nobg.png",
        alt: "Engineer Morty fine-tuning the platform",
        width: 300,
        height: 300,
      }}
    />
  );

  return (
    <RoutePageShell
      eyebrow="Platform"
      title="Meet Morty: Your Visual Retrieval Buddy"
      description="Discover how Morty combines Vultr's global infrastructure with ColPali's advanced vision models to revolutionize how you interact with documents."
      meta={heroMeta}
      variant="compact"
    >
      <motion.div
        className="mx-auto flex w-full max-w-5xl flex-col gap-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* Meet Morty Hero Section */}
        <motion.section
          className="rounded-3xl border border-vultr-blue/20 bg-gradient-to-br from-vultr-blue/5 via-white to-purple-500/5 p-8 shadow-sm dark:from-vultr-blue-20/20 dark:via-vultr-midnight dark:to-purple-500/10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="space-y-6">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-full bg-vultr-blue/10 px-4 py-2 text-body-sm font-semibold text-vultr-blue">
                <Sparkles className="size-icon-xs" />
                Meet Your Visual Intelligence Companion
              </div>
              <h2 className="text-editorial-h2 font-bold text-vultr-navy dark:text-white">
                Morty: More Than a Mascot
              </h2>
              <p className="text-body-lg text-vultr-navy/70 dark:text-white/70">
                Morty isn't just Vultr's friendly face - he's your intelligent Visual Retrieval Buddy who understands documents the way humans do. Powered by cutting-edge ColPali vision models and Vultr's global infrastructure, Morty sees charts, reads layouts, and finds exactly what you're looking for.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-center gap-3 rounded-xl border border-vultr-blue/20 bg-white/50 p-4 dark:bg-vultr-midnight/50">
                <div className="flex size-10 items-center justify-center rounded-full bg-vultr-blue/10 text-vultr-blue">
                  <Sparkles className="size-icon-sm" />
                </div>
                <div>
                  <h3 className="font-semibold text-vultr-navy dark:text-white">Visual Intelligence</h3>
                  <p className="text-body-xs text-vultr-navy/70 dark:text-white/70">Understands images, charts, and layouts</p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-vultr-blue/20 bg-white/50 p-4 dark:bg-vultr-midnight/50">
                <div className="flex size-10 items-center justify-center rounded-full bg-vultr-blue/10 text-vultr-blue">
                  <Rocket className="size-icon-sm" />
                </div>
                <div>
                  <h3 className="font-semibold text-vultr-navy dark:text-white">Lightning Fast</h3>
                  <p className="text-body-xs text-vultr-navy/70 dark:text-white/70">Powered by Vultr's global GPU network</p>
                </div>
              </div>
            </div>
          </div>
        </motion.section>

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
                <CardTitle className="text-digital-h4 font-semibold text-balance">Morty's Technology Stack</CardTitle>
                <CardDescription className="max-w-3xl text-body-sm leading-relaxed">
                  Each service in Morty's arsenal is optimized for fast setup on Vultr infrastructure. Customize how Morty processes your documents without rebuilding the experience.
                </CardDescription>
              </div>
              <AppButton asChild variant="outline" size="sm" className="rounded-[var(--radius-button)]">
                <Link href="/configuration">Configure Morty</Link>
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
              <CardTitle className="text-digital-h5 font-semibold text-balance">Built for Morty's Intelligence</CardTitle>
              <CardDescription className="text-body-sm leading-relaxed">
                Every component works together to power Morty's visual understanding and friendly personality.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-body-sm text-muted-foreground">
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/70 p-3 dark:border-white/15 dark:bg-vultr-midnight/50 text-body-xs ">
                <Braces className="size-icon-xs text-primary" />
                <span>Morty's responses stay consistent through generated TypeScript clients synced with FastAPI routes.</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/70 p-3 dark:border-white/15 dark:bg-vultr-midnight/50 text-body-xs ">
                <Workflow className="size-icon-xs text-primary" />
                <span>Shared event bus keeps Morty's upload, search, and chat features perfectly synchronized.</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/70 p-3 dark:border-white/15 dark:bg-vultr-midnight/50 text-body-xs ">
                <Rocket className="size-icon-xs text-primary" />
                <span>Docker-first setup mirrors local testing and Vultr production for Morty's deployment.</span>
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
            <h2 className="text-editorial-h3 font-semibold">From PDF to Morty's grounded answer</h2>
            <p className="text-body-sm text-muted-foreground sm:text-body">
              Follow Morty's intelligent workflow as he transforms your documents into searchable, visual knowledge that you can chat with naturally.
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
          <h2 className="text-editorial-h3 font-semibold">Ready to experience Morty's intelligence?</h2>
          <p className="mt-3 text-body-sm text-muted-foreground sm:text-body">
            Bring your documents to Morty and watch him work his visual magic. Upload your PDFs, ask him questions, and discover what makes your Visual Retrieval Buddy special. Start building smarter document workflows with Morty today.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
            <AppButton asChild size="lg" variant="cta" elevated iconShift>
              <Link href="/chat">
                Chat with Morty
                <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
              </Link>
            </AppButton>
            <AppButton asChild size="lg" variant="outline" elevated iconShift>
              <Link href="/upload">
                Upload for Morty
                <ArrowRight className="size-icon-xs transition-transform group-hover/app-button:translate-x-1" />
              </Link>
            </AppButton>
          </div>
        </motion.section>
      </motion.div>
    </RoutePageShell>
  );
}

