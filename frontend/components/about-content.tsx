import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Layers, Database, Server, Brain, ArrowRight } from "lucide-react";

const STACK_ITEMS = [
  {
    icon: Layers,
    title: "Frontend",
    description: "Next.js 15 with Tailwind v4 and shadcn components for a clean, mobile-friendly UI.",
  },
  {
    icon: Server,
    title: "Backend",
    description: "FastAPI exposes ingestion, retrieval, configuration, and health endpoints.",
  },
  {
    icon: Database,
    title: "Storage & search",
    description: "Qdrant stores multi-vector embeddings, MinIO handles page imagery.",
  },
  {
    icon: Brain,
    title: "Vision model",
    description: "Snappy ships with ColQwen2.5 so queries understand text and layout together.",
  },
] as const;

export default function AboutContent() {
  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-foreground">Snappy in a nutshell</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Snappy is a template that helps you build visual retrieval experiences quickly. Upload slide decks, scans, or
          reports and you get ingestion, semantic search, and chat with visual citations. Everything runs locally, so
          you can customise the experience before pointing it at your own data.
        </p>
        <Badge variant="secondary" className="rounded-full">FastAPI · Next.js · ColQwen2.5</Badge>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {STACK_ITEMS.map(({ icon: Icon, title, description }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center gap-3 pb-3">
              <span className="inline-flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </span>
              <CardTitle className="text-base font-semibold">{title}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">{description}</CardContent>
          </Card>
        ))}
      </section>

      <section className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Quick start</CardTitle>
            <CardDescription>
              Three steps and you are ready to explore your documents.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p><strong className="text-foreground">1. Ingest</strong> – Upload PDFs or images on the Upload tab.</p>
            <p><strong className="text-foreground">2. Search</strong> – Use natural language to find matching pages.</p>
            <p><strong className="text-foreground">3. Chat</strong> – Ask questions and verify answers with page previews.</p>
          </CardContent>
        </Card>

        <div className="rounded-xl border border-dashed border-muted p-6">
          <h3 className="text-lg font-semibold text-foreground">Want to customise?</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            The repository includes backend, frontend, and embedding services. Visit the docs to see configuration guides,
            API references, and deployment tips.
          </p>
          <Button asChild variant="outline" className="mt-4">
            <Link href="https://github.com/athrael-soju/snappy-template" target="_blank" rel="noreferrer">
              Open documentation
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
