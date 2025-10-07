"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles } from "lucide-react";

const workflow = [
  {
    title: "Upload",
    description: "Drag & drop your documents for ingestion",
    icon: CloudUpload,
  },
  {
    title: "Process",
    description: "ColPali extracts visual embeddings automatically",
    icon: Database,
  },
  {
    title: "Search & Chat",
    description: "Ask questions or browse visual results instantly",
    icon: Brain,
  },
];

export default function Home() {
  return (
    <motion.div {...defaultPageMotion} className="page-shell flex min-h-0 flex-1 flex-col">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-8 pt-8 sm:pt-12">
        <PageHeader
          title="FastAPI / Next.js / ColPali Template"
          description="This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the boilerplate."
          icon={Sparkles}
          badge={<Badge className="rounded-full text-sm">v0.0.4</Badge>}
        >
          <div className="flex flex-col items-center gap-5">
            <div className="flex flex-col items-center gap-3 text-sm text-muted-foreground max-w-2xl">
              <p className="text-base text-foreground/90">
                Spin up ingestion, visual search, and chat workflows in minutes with opinionated defaults and accessible UI patterns.
              </p>
            </div>
            <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4">
              <Button
                asChild
                size="lg"
                className="primary-gradient rounded-full px-7 py-4 text-base shadow-lg transition-transform focus-visible:ring-4 focus-visible:ring-ring/35 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)] hover:-translate-y-0.5"
              >
                <Link href="/upload">
                  <CloudUpload className="mr-3 h-5 w-5" />
                  Upload your documents
                  <ArrowRight className="ml-3 h-5 w-5" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="rounded-full border-muted bg-[color:var(--surface-0)]/80 px-6 py-[0.875rem] text-base text-foreground transition hover:bg-[color:var(--surface-1)] focus-visible:ring-2 focus-visible:ring-ring/35 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)]"
              >
                <Link href="/search">Explore search</Link>
              </Button>
            </div>
          </div>
        </PageHeader>
      </motion.section>

      <section className="flex-1 min-h-0 pb-8 sm:pb-12">
        <ScrollArea className="h-full overflow-hidden">
          <div className="p-4">
            <motion.div className="grid gap-6 md:grid-cols-3" {...staggeredListMotion}>
          {workflow.map(({ title, description, icon: Icon }) => (
            <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
              <Card className="card-surface h-full">
                <CardHeader className="flex flex-row items-center gap-4 border-b border-divider pb-4">
                  <div className="flex size-12 items-center justify-center rounded-xl border border-muted bg-[color:var(--surface-2)] text-primary">
                    <Icon className="h-5 w-5" strokeWidth={2.2} />
                  </div>
                  <CardTitle className="text-xl font-semibold text-foreground">{title}</CardTitle>
                </CardHeader>
                <CardContent className="pt-4 text-sm leading-relaxed text-muted-foreground">
                  {description}
                </CardContent>
              </Card>
            </motion.div>
          ))}
            </motion.div>
          </div>
        </ScrollArea>
      </section>
    </motion.div>
  );
}
