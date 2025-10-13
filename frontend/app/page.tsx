"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  defaultPageMotion,
  fadeInItemMotion,
  hoverLift,
  sectionVariants,
  staggeredListMotion,
} from "@/lib/motion-presets";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Brain, CloudUpload, Database, Loader2, Sparkles } from "lucide-react";
import { FeatureCard } from "@/components/ui/feature-card";

const workflow = [
  {
    title: "Load your library fast",
    description: "Drop PDFs, decks, and scans. Snappy neatly ingests every page.",
    icon: CloudUpload,
    href: "/upload",
    badges: ["Batch Upload", "Auto-tagged"],
    features: [
      "Ingest batches in minutes with drag-and-drop progress you can follow",
      "Keep uploads clean thanks to smart validation",
      "Know what's ready with friendly status lights",
    ],
    accent: "primary" as const,
  },
  {
    title: "Find what matters",
    description: "Visual embeddings unlock layout-aware search you can trust.",
    icon: Database,
    href: "/maintenance?section=configuration",
    badges: ["Vector Search", "GPU Friendly"],
    features: [
      "Surface the right page in seconds via vision-first indexing",
      "Shape your workspace with flexible metadata tools",
      "Stay confident with always-on Snappy health checks",
    ],
    accent: "accent" as const,
  },
  {
    title: "Ask & verify",
    description: "Ask a question, get grounded answers with cited snapshots.",
    icon: Brain,
    href: "/search",
    badges: ["Chat Ready", "Citations"],
    features: [
      "Ask naturally and search every page instantly",
      "Trust matches with instant visual citations",
      "Keep context alive through conversational chat",
    ],
    accent: "secondary" as const,
  },
];

export default function Home() {
  const [showHeroChip, setShowHeroChip] = useState(true);
  const [demoLoading, setDemoLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => setShowHeroChip(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleDemoClick = useCallback(() => {
    setDemoLoading(true);
    router.push("/search?demo=true");
  }, [router]);

  return (
    <motion.div {...defaultPageMotion} className="page-shell flex min-h-0 flex-1 flex-col">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
        <PageHeader
          title="Ask your documents. Get cited answers."
          icon={Sparkles}
          badge={
            <Badge className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              Vision Retrieval Buddy
            </Badge>
          }
          tooltip="Snappy keeps visual documents searchable and friendly so your team can share answers faster."
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 pb-6 sm:pb-8 flex">
        <ScrollArea className="h-[calc(100vh-12rem)] rounded-xl">
          <div className="mx-auto max-w-6xl px-4 py-6">
            <div className="mb-10 flex flex-col items-center gap-8 text-center sm:mb-12">
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="max-w-3xl space-y-4"
              >
                <AnimatePresence>
                  {showHeroChip && (
                    <motion.div
                      className="hidden items-center gap-2 rounded-full border border-border/60 bg-card/70 px-3 py-1 text-xs font-semibold text-muted-foreground/90 sm:inline-flex"
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                    >
                      <Sparkles className="h-3.5 w-3.5 text-primary" />
                      Snappy says hi
                    </motion.div>
                  )}
                </AnimatePresence>
                <h2 className="text-3xl font-semibold leading-tight tracking-tight text-foreground sm:text-[2.75rem]">
                  Instant answers from your slides, scans, and PDFs - with receipts.
                </h2>
                <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
                  <span className="font-semibold text-primary">Snappy</span> gives you answers with visual citations you can verify.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, ease: "easeOut", delay: 0.05 }}
                className="flex flex-col items-center gap-4 sm:flex-row sm:gap-5"
              >
                <Button
                  type="button"
                  size="lg"
                  aria-busy={demoLoading}
                  onClick={handleDemoClick}
                  className="primary-gradient rounded-full px-8 py-5 text-base font-semibold shadow-lg transition-all hover:-translate-y-0.5 hover:shadow-xl focus-visible:ring-4 focus-visible:ring-ring/35 focus-visible:ring-offset-2"
                >
                  {demoLoading ? (
                    <span className="inline-flex items-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Launching demo...
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-2">
                      Try a live demo
                      <span aria-hidden="true" className="text-lg leading-none">
                        &rarr;
                      </span>
                    </span>
                  )}
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="rounded-full px-6 py-5 text-base font-medium sm:px-7"
                >
                  <Link href="/upload">
                    <CloudUpload className="mr-2 h-5 w-5" />
                    Add your docs
                  </Link>
                </Button>
              </motion.div>
              <p className="text-xs font-medium text-muted-foreground/80 sm:text-sm">
                No setup - see it work in 10 seconds.
              </p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: "easeOut", delay: 0.12 }}
                className="w-full max-w-3xl overflow-hidden rounded-[calc(var(--radius-lg)+1rem)] border border-border/60 bg-card/80 shadow-md"
              >
                <div className="relative grid gap-4 p-6 sm:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] sm:p-8">
                  <div className="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full border border-border/60 bg-card/80 px-3 py-1 text-xs font-semibold text-muted-foreground">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    Cited snapshot
                  </div>
                  <div className="mt-10 space-y-3 text-left sm:mt-0">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground/80">
                      Question
                    </span>
                    <p className="text-lg font-semibold text-foreground">
                      "Show me the budget summary for Q3."
                    </p>
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      Snappy pinpoints the right slide, highlights the data you need, and cites the page before you share the answer.
                    </p>
                  </div>
                  <div className="relative flex items-center justify-center rounded-2xl border border-border/60 bg-card/90 p-4 sm:p-5">
                    <div className="absolute right-4 top-4 rounded-full border border-border/50 bg-card px-3 py-1 text-xs font-semibold text-muted-foreground">
                      Page 5 - cited
                    </div>
                    <div className="flex aspect-[3/4] w-full items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-primary/10 via-background to-secondary/10 shadow-inner">
                      <div className="flex flex-col items-center gap-3 text-center">
                        <span className="rounded-full border border-border/60 bg-card/80 px-3 py-1 text-xs font-semibold text-muted-foreground">
                          Document preview
                        </span>
                        <span className="text-[11px] text-muted-foreground">
                          Visual citation ready to drop into your notes.
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>

            <motion.div className="grid gap-5 sm:grid-cols-2 sm:gap-6 lg:grid-cols-3" {...staggeredListMotion}>
              {workflow.map(({ title, description, icon, href, badges, features, accent }) => (
                <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
                  <Link
                    href={href}
                    className="block h-full rounded-[calc(var(--radius-lg)+0.5rem)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <FeatureCard
                      icon={icon}
                      title={title}
                      description={description}
                      badges={badges}
                      features={features}
                      accent={accent}
                    />
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </ScrollArea>
      </motion.section>
    </motion.div>
  );
}

