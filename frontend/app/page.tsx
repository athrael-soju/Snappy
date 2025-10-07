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
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
        <PageHeader
          title="FastAPI / Next.js / ColPali Template"
          icon={Sparkles}
          badge={<Badge className="rounded-full text-sm">v0.0.4</Badge>}
          tooltip="This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the boilerplate"
        >
          <div className="flex flex-col items-center gap-5">
            <div className="flex flex-col items-center gap-3 text-sm max-w-2xl">
              <p className="text-base text-foreground font-medium">
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
                className="rounded-full border-2 border-border bg-card px-6 py-[0.875rem] text-base text-foreground font-medium transition hover:bg-[color:var(--surface-2)] hover:border-border-strong focus-visible:ring-2 focus-visible:ring-ring/35 focus-visible:ring-offset-2"
              >
                <Link href="/search">Explore search</Link>
              </Button>
            </div>
          </div>
        </PageHeader>
      </motion.section>

      <section className="flex-1 min-h-0 pb-6 sm:pb-8">
        <ScrollArea className="custom-scrollbar h-[calc(100vh-26rem)]">
          <div className="px-4 py-6">
            <motion.div className="grid gap-6 md:grid-cols-3 max-w-7xl mx-auto" {...staggeredListMotion}>
          {workflow.map(({ title, description, icon: Icon }) => (
            <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
              <Card className="card-surface h-full hover:shadow-xl transition-all duration-300 border-border/50">
                <CardHeader className="flex flex-row items-center gap-4 border-b border-divider pb-5">
                  <div className="flex size-14 items-center justify-center rounded-xl border-2 border-primary/20 bg-gradient-to-br from-primary/10 to-primary/5 text-primary shadow-sm">
                    <Icon className="h-6 w-6" strokeWidth={2.2} />
                  </div>
                  <CardTitle className="text-xl font-bold text-foreground tracking-tight">{title}</CardTitle>
                </CardHeader>
                <CardContent className="pt-5 text-sm leading-relaxed text-foreground/90 font-medium">
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
