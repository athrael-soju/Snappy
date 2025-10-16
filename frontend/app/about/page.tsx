"use client";

import Link from "next/link";
import {
  Sparkles,
  Database,
  Cloud,
  Server,
  Globe,
  Brain,
  Settings,
  Scan,
  Image as ImageIcon,
  FileText,
  Layers,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

const projectSummary = [
  "Full-stack multimodal RAG system using FastAPI, Next.js, and ColQwen2.5 for visual document understanding.",
  "Optimized for scanned documents, forms, tables, and complex layouts where text-only RAG struggles.",
];

const keyFeatures = [
  {
    icon: Database,
    title: "Qdrant Vector Engine",
    description: "Binary quantization, multi-vector search, optional MUVERA.",
  },
  {
    icon: Cloud,
    title: "MinIO Storage Pipeline",
    description: "Parallel uploads (12 workers), JPEG quality control, public URLs.",
  },
  {
    icon: Server,
    title: "FastAPI Orchestration",
    description: "Pipelined indexing (3-batch concurrency), SSE progress streaming.",
  },
  {
    icon: Globe,
    title: "Next.js 15 Interface",
    description: "Edge Runtime chat, localStorage config, real-time UI.",
  },
  {
    icon: Brain,
    title: "ColQwen2.5 Embeddings",
    description: "Multi-vector embeddings with mean pooling across rows and columns.",
  },
  {
    icon: Settings,
    title: "Operational Controls",
    description: "Runtime config UI, health checks, maintenance endpoints.",
  },
];

const colpaliDetails = [
  "ColPali = Contextualized Late Interaction over PaliGemma; retrieves using page-image multi-vector embeddings (no OCR).",
  "Uses ColQwen2.5 (7B VLM) tuned for document understanding.",
  "Produces 128 patch embeddings per image (each 1024D); queries scored via MaxSim (max similarity between query tokens and image patches).",
  "Adds row/column mean-pooled vectors for both fine-grained and holistic retrieval.",
  "Binary quantization (~32x) speeds search; full-precision rescoring preserves accuracy.",
  "Excels when layout/typography/tables/charts/handwriting carry meaning.",
];

const ragComparison = [
  {
    title: "Traditional RAG",
    icon: FileText,
    accent: "Text-first",
    bullets: [
      "Needs OCR/PDF text parsing.",
      "Fast on clean, well-formatted docs.",
      "Loses layout; struggles with tables/charts/handwriting.",
      "Compact text chunks (~512 tokens).",
      "Best for blogs, documentation, clean PDFs.",
    ],
  },
  {
    title: "ColPali",
    icon: ImageIcon,
    accent: "Visual-first",
    bullets: [
      "No OCR; works directly on images.",
      "128 patch embeddings/page + multi-vector search.",
      "Preserves layout; naturally handles tables/charts/handwriting.",
      "Larger vectors (128x1024D) but 32x compressed via quantization.",
      "Best for scanned docs, forms, receipts, complex layouts.",
    ],
  },
];

const techStack = [
  {
    title: "Backend (Python/FastAPI)",
    icon: Server,
    items: [
      "Modular routers",
      "Pipelined indexing (3-batch)",
      "SSE progress streaming",
      "Runtime config API",
    ],
  },
  {
    title: "Frontend (Next.js 15/React)",
    icon: Globe,
    items: [
      "Edge Runtime chat",
      "shadcn/ui + Tailwind",
      "OpenAPI SDK + Zod",
      "Zustand + localStorage",
    ],
  },
  {
    title: "Vector DB (Qdrant)",
    icon: Database,
    items: [
      "Binary quantization (32×)",
      "Multi-vector search",
      "Optional MUVERA",
      "On-disk storage",
    ],
  },
  {
    title: "Storage (MinIO)",
    icon: Cloud,
    items: [
      "Parallel uploads (12 workers)",
      "JPEG/PNG/WebP support",
      "Public URL generation",
      "Retry logic + fail-fast",
    ],
  },
];

const usageGuidelines = [
  {
    title: "Choose Text-only RAG when:",
    icon: FileText,
    items: [
      "Docs are clean, digital-native (blogs, code, markdown).",
      "Tight storage/compute budgets.",
      "Visual layout doesn’t matter.",
    ],
  },
  {
    title: "Choose ColPali when:",
    icon: ImageIcon,
    items: [
      "Docs are scanned or have complex tables/charts/handwriting.",
      "Layout carries semantics (forms, invoices, receipts).",
      "OCR is poor/unreliable.",
      "You need high recall on visual/spatial cues.",
    ],
  },
];

const gettingStartedSteps = [
  {
    title: "Upload Documents",
    description: "Upload PDFs, forms, or scans for automatic processing. (/upload)",
  },
  {
    title: "Search Documents",
    description: "Use natural language with visual understanding. (/search)",
  },
  {
    title: "Chat with AI",
    description: "Ask questions; answers include visual citations. (/chat)",
  },
  {
    title: "Maintenance",
    description: "Manage data, configure settings, monitor health. (/maintenance)",
  },
];

const docsUrl = "https://github.com/athrael-soju/fastapi-nextjs-colpali-template";

export default function AboutPage() {
  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-6">
          <div className="shrink-0 space-y-3 text-center">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                About the
              </span>{" "}
              <span className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                ColPali RAG Template
              </span>
            </h1>
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground sm:text-sm">
              Visual-first retrieval that pairs a FastAPI backend with a Next.js front-end and ColQwen2.5 multimodal embeddings to understand documents beyond plain text.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Sparkles className="h-3 w-3 text-purple-500" />
                Multimodal RAG
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <ImageIcon className="h-3 w-3 text-blue-500" />
                Layout Aware
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                Production Ready
              </Badge>
            </div>
          </div>

          <ScrollArea className="min-h-0 flex-1">
            <div className="space-y-6 pr-4 pb-8">
              <Card className="border-border/60 bg-card/60 backdrop-blur">
                <CardHeader className="items-start gap-2">
                  <div className="flex items-center gap-2 text-primary">
                    <Sparkles className="h-5 w-5" />
                    <CardTitle className="text-lg">Project Overview</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
                  {projectSummary.map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                  ))}
                </CardContent>
              </Card>

              <section className="space-y-3">
                <div className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Key Features</h2>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {keyFeatures.map((feature) => {
                    const Icon = feature.icon;
                    return (
                      <Card
                        key={feature.title}
                        className="border-border/60 bg-card/60 transition-colors hover:border-primary/40"
                      >
                        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <Icon className="h-5 w-5" />
                          </div>
                          <CardTitle className="text-sm">{feature.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm leading-relaxed text-muted-foreground">
                            {feature.description}
                          </p>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </section>

              <Card className="border-border/60 bg-card/60">
                <CardHeader className="items-start gap-2">
                  <div className="flex items-center gap-2 text-primary">
                    <Scan className="h-5 w-5" />
                    <CardTitle className="text-lg">What is ColPali?</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
                    {colpaliDetails.map((detail) => (
                      <li key={detail}>{detail}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <section className="space-y-3">
                <div className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">ColPali vs. Text-only RAG</h2>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {ragComparison.map((option) => {
                    const Icon = option.icon;
                    return (
                      <Card
                        key={option.title}
                        className="border-border/60 bg-card/60"
                      >
                        <CardHeader className="gap-3">
                          <div className="flex items-center gap-2">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                              <Icon className="h-5 w-5" />
                            </div>
                            <div>
                              <CardTitle className="text-sm">{option.title}</CardTitle>
                              <Badge variant="secondary" className="mt-1 px-2 py-0.5 text-[10px] uppercase tracking-wide">
                                {option.accent}
                              </Badge>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
                            {option.bullets.map((bullet) => (
                              <li key={bullet}>{bullet}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2">
                  <Server className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Technical Stack & Features</h2>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {techStack.map((block) => {
                    const Icon = block.icon;
                    return (
                      <Card
                        key={block.title}
                        className="border-border/60 bg-card/60"
                      >
                        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <Icon className="h-5 w-5" />
                          </div>
                          <CardTitle className="text-sm">{block.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
                            {block.items.map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">When should I use it?</h2>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {usageGuidelines.map((guideline) => {
                    const Icon = guideline.icon;
                    return (
                      <Card
                        key={guideline.title}
                        className="border-border/60 bg-card/60"
                      >
                        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <Icon className="h-5 w-5" />
                          </div>
                          <CardTitle className="text-sm">{guideline.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
                            {guideline.items.map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
                <Card className="border-dashed border-primary/40 bg-primary/5 text-sm leading-relaxed text-primary">
                  <CardContent className="flex items-center gap-2 py-4">
                    <ArrowRight className="h-4 w-4" />
                    Hybrid approach: Use ColPali for visual-heavy pages and text embeddings for clean docs.
                  </CardContent>
                </Card>
              </section>

              <Card className="border-border/60 bg-card/60">
                <CardHeader className="items-start gap-2">
                  <div className="flex items-center gap-2 text-primary">
                    <Sparkles className="h-5 w-5" />
                    <CardTitle className="text-lg">Getting Started (4 Steps)</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <ol className="space-y-3">
                    {gettingStartedSteps.map((step, index) => (
                      <li key={step.title} className="flex items-start gap-3 text-sm leading-relaxed text-muted-foreground">
                        <Badge variant="secondary" className="mt-1 h-6 w-6 shrink-0 items-center justify-center rounded-full px-0 text-xs font-semibold">
                          {index + 1}
                        </Badge>
                        <div>
                          <p className="font-medium text-foreground">{step.title}</p>
                          <p>{step.description}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </CardContent>
              </Card>

              <Card className="border-primary/40 bg-primary/5">
                <CardContent className="flex flex-col items-start gap-4 py-6 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-primary">
                      Docs
                    </p>
                    <p className="text-sm text-muted-foreground">
                      View documentation on GitHub -&gt;
                    </p>
                  </div>
                  <Button asChild variant="outline" className="gap-2">
                    <Link href={docsUrl} target="_blank" rel="noreferrer">
                      Open Repository
                      <ExternalLink className="h-4 w-4" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
