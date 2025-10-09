import Link from "next/link";
import {
  Brain,
  CloudUpload,
  Eye,
  Layers,
  Shield,
  Sparkles,
  Wand2,
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const highlights = [
  {
    icon: Sparkles,
    title: "Friendly from Day One",
    description:
      "Snappy wraps document ingestion, visual retrieval, and chat in a calm interface that gets out of your way.",
    badge: "All-in-one",
  },
  {
    icon: Layers,
    title: "Vision-First Understanding",
    description:
      "Every page is encoded as multi-vector embeddings, so layouts, tables, and handwriting stay searchable.",
    badge: "Layout aware",
  },
  {
    icon: Shield,
    title: "Operational Confidence",
    description:
      "Health checks, status toasts, and clear progress keep admins confident that pipelines are humming.",
    badge: "Built for teams",
  },
] as const;

const steps = [
  {
    number: "1",
    title: "Load Documents",
    icon: CloudUpload,
    description:
      "Drag in PDFs, slides, or images. Snappy validates formats, batches uploads, and shows progress in real time.",
    href: "/upload",
    cta: "Add documents",
  },
  {
    number: "2",
    title: "Review the Library",
    icon: Eye,
    description:
      "Behind the scenes Snappy creates vector embeddings (powered by ColQwen2.5) so every page is searchable by meaning and layout.",
    href: "/maintenance?section=configuration",
    cta: "Tune settings",
  },
  {
    number: "3",
    title: "Ask & Explore",
    icon: Brain,
    description:
      "Use natural language to search or chat. Snappy returns cited answers with visual previews you can trust.",
    href: "/search",
    cta: "Start searching",
  },
] as const;

const quickLinks = [
  {
    title: "Upload Center",
    description: "Batch ingest files with instant feedback and retry controls.",
    href: "/upload",
    icon: CloudUpload,
    badge: "Workspace",
  },
  {
    title: "Search Hub",
    description: "Run visual retrieval, filter by metadata, and preview hits.",
    href: "/search",
    icon: Eye,
    badge: "Retrieval",
  },
  {
    title: "Chat Desk",
    description: "Hold grounded conversations backed by cited evidence.",
    href: "/chat",
    icon: Brain,
    badge: "Conversational",
  },
] as const;

export default function AboutContent({ onClose }: { onClose?: () => void }) {
  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <Card className="border border-border/60 bg-card/80 backdrop-blur">
        <CardHeader className="gap-4 text-left">
          <Badge variant="outline" className="self-start border-primary/30 text-primary">
            Meet Snappy
          </Badge>
          <CardTitle className="text-2xl font-semibold text-foreground">
            Your friendly vision retrieval buddy
          </CardTitle>
          <CardDescription className="text-base text-muted-foreground leading-relaxed">
            Snappy connects a FastAPI backend, Qdrant vector search, and a modern Next.js front end so teams can see
            their knowledge in one place. The UI stays simple while the engine pairs visual embeddings with chat that
            cites its sources.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          {highlights.map(({ icon: Icon, title, description, badge }) => (
            <div key={title} className="rounded-2xl border border-border/50 bg-card/70 p-4 shadow-sm">
              <div className="flex items-center gap-2 text-primary">
                <Icon className="h-5 w-5" />
                <span className="text-xs font-medium uppercase tracking-wide text-primary/80">{badge}</span>
              </div>
              <h3 className="mt-3 text-base font-semibold text-foreground">{title}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{description}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border border-border/60 bg-card/80 backdrop-blur">
        <CardHeader>
          <Badge variant="secondary" className="w-fit">
            How it works
          </Badge>
          <CardTitle className="text-xl font-semibold text-foreground">
            Three simple steps from upload to insight
          </CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            Everything runs asynchronously so you can keep working while Snappy ingests, indexes, and answers.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {steps.map(({ number, title, icon: Icon, description, href, cta }) => (
            <div
              key={number}
              className="flex flex-col gap-3 rounded-2xl border border-border/50 bg-card/70 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold">
                  {number}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-primary" />
                    <h3 className="text-base font-semibold text-foreground">{title}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
                </div>
              </div>
              <Button asChild variant="ghost" className="self-start rounded-full px-4 text-sm">
                <Link href={href} onClick={() => onClose?.()}>
                  {cta}
                </Link>
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border border-border/60 bg-card/80 backdrop-blur">
        <CardHeader>
          <Badge variant="outline" className="w-fit border-primary/30 text-primary">
            Under the hood
          </Badge>
          <CardTitle className="text-xl font-semibold text-foreground">Why Snappy feels so responsive</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            We keep the UI relaxed but the stack is serious about performance and accuracy.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="grid gap-4 sm:grid-cols-2">
            {[
              {
                title: "Multi-vector embeddings",
                description:
                  "Pages are encoded with ColQwen2.5 to preserve layout, tables, and handwriting, yielding precise matches.",
              },
              {
                title: "Qdrant vector search",
                description:
                  "Binary-quantized indexes balance speed and recall, while metadata filters keep queries targeted.",
              },
              {
                title: "FastAPI orchestrator",
                description:
                  "Batch ingestion, SSE progress streaming, and health checks keep the pipeline transparent.",
              },
              {
                title: "Next.js experience",
                description:
                  "A modern React front end with optimistic updates, light/dark theming, and reusable UI primitives.",
              },
            ].map((item) => (
              <li key={item.title} className="rounded-2xl border border-border/40 bg-card/70 p-4 shadow-sm">
                <h3 className="text-base font-semibold text-foreground">{item.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{item.description}</p>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="border border-border/60 bg-card/80 backdrop-blur">
        <CardHeader className="flex flex-col gap-2">
          <Badge variant="secondary" className="w-fit">
            Quick links
          </Badge>
          <CardTitle className="text-xl font-semibold text-foreground">Jump back into Snappy</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            These shortcuts close the dialog and take you straight to the most-used areas.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          {quickLinks.map(({ title, description, href, icon: Icon, badge }) => (
            <div key={title} className="flex h-full flex-col justify-between rounded-2xl border border-border/40 bg-card/70 p-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-primary">
                  <Icon className="h-4 w-4" />
                  <span className="text-xs font-medium uppercase tracking-wide text-primary/80">{badge}</span>
                </div>
                <h3 className="text-base font-semibold text-foreground">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
              </div>
              <Button asChild variant="ghost" className="mt-4 w-full rounded-full text-sm">
                <Link href={href} onClick={() => onClose?.()}>
                  Open
                </Link>
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
        <Wand2 className="h-4 w-4 text-primary" />
        <p>
          Want to extend Snappy? Swap in your preferred embedding model, adjust the ingestion concurrency, or theme the UI
          with Tailwind tokens—everything is ready.
        </p>
      </div>
    </div>
  );
}
