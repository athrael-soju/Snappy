import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  Sparkles,
  CloudUpload,
  Eye,
  MessageCircle,
  Cog,
  Server,
  ShieldCheck,
} from "lucide-react";

const pillars = [
  {
    title: "Visual context first",
    description:
      "Snappy keeps page layout, tables, illustrations, and handwriting intact with ColPali multi-vector embeddings so answers stay true to what people see.",
    icon: Eye,
  },
  {
    title: "Operational confidence built-in",
    description:
      "FastAPI powers streaming ingestion, MinIO storage, Qdrant collections, and health checks—all exposed through a friendly maintenance surface.",
    icon: Cog,
  },
  {
    title: "A calm front of house",
    description:
      "Next.js 15, shared stores, and thoughtful defaults give teams a approachable UI that is easy to extend without design debt.",
    icon: Sparkles,
  },
] as const;

const workflow = [
  {
    step: "1. Drop your files",
    detail:
      "Upload PDFs or images in batches. Snappy keeps you updated with realtime progress while MinIO stores the generated pages.",
    icon: CloudUpload,
    href: "/upload",
    cta: "Open upload",
  },
  {
    step: "2. Explore visually",
    detail:
      "Search with natural language and filter with confidence. Snappy returns the exact page snippets that scored highest in Qdrant.",
    icon: Eye,
    href: "/search",
    cta: "Try search",
  },
  {
    step: "3. Chat with citations",
    detail:
      "Ask conversational questions and stream responses that reference the same visual evidence your teammates will see.",
    icon: MessageCircle,
    href: "/chat",
    cta: "Start chatting",
  },
] as const;

const stack = [
  {
    title: "FastAPI + Qdrant + MinIO",
    description:
      "Handles ingestion pipelines, binary quantization toggles, health endpoints, and vector storage with optional MUVERA reranking.",
    icon: Server,
  },
  {
    title: "ColPali embeddings",
    description:
      "Powered by ColQwen2.5. Page images are embedded into patch vectors so Snappy can match questions against visual details.",
    icon: ShieldCheck,
  },
  {
    title: "Next.js 15 frontend",
    description:
      "App router, server actions, shadcn/ui components, and state stores ready for customization or white-labeling.",
    icon: Sparkles,
  },
] as const;

export default function AboutContent({ onClose }: { onClose?: () => void }) {
  return (
    <div className="space-y-8">
      <section className="grid gap-4 sm:grid-cols-3">
        {pillars.map(({ title, description, icon: Icon }) => (
          <Card key={title} className="border-border/60">
            <CardHeader className="space-y-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </span>
              <CardTitle className="text-lg">{title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline" className="border-primary/40 bg-primary/10 text-primary">
              Workflow
            </Badge>
            <span>Three steps from raw documents to trustworthy answers.</span>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {workflow.map(({ step, detail, icon: Icon, href, cta }) => (
            <Card key={step} className="flex h-full flex-col border-border/60">
              <CardHeader className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <CardTitle className="text-base font-semibold">{step}</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col justify-between gap-4">
                <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                  {detail}
                </CardDescription>
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                  className="w-full rounded-lg"
                >
                  <Link href={href} onClick={() => onClose?.()}>
                    {cta}
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <Card className="border-border/60">
          <CardHeader className="space-y-3">
            <CardTitle className="text-xl font-semibold">Under the hood</CardTitle>
            <CardDescription className="text-sm text-muted-foreground">
              Snappy keeps a pragmatic stack so you can run it locally, on-prem, or in production without surprises.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            {stack.map(({ title, description, icon: Icon }) => (
              <div key={title} className="space-y-2 rounded-2xl border border-border/60 bg-card/60 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <Icon className="h-4 w-4 text-primary" />
                  {title}
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">{description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section className="flex flex-col gap-3 rounded-3xl border border-border/60 bg-card/70 p-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">Keep exploring Snappy</h3>
          <p>
            Snappy is open-source and ready for your workflow. Clone it, fork it, and make it your own.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button asChild variant="default" className="rounded-lg">
            <Link
              href="https://github.com/athrael-soju/fastapi-nextjs-colpali-template"
              target="_blank"
              rel="noreferrer"
              onClick={() => onClose?.()}
            >
              View repository
            </Link>
          </Button>
          <Button asChild variant="outline" className="rounded-lg">
            <Link
              href="https://github.com/athrael-soju/fastapi-nextjs-colpali-template/blob/main/feature-list.md"
              target="_blank"
              rel="noreferrer"
              onClick={() => onClose?.()}
            >
              Feature checklist
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
