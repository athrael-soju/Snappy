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
          tooltip="This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the configuration"
        >
          <div className="flex flex-col items-center gap-5">
            <div className="flex flex-col items-center gap-3 text-sm max-w-2xl">
            </div>
            <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4">
              <Button
                asChild
                size="lg"
                className="primary-gradient rounded-full px-8 py-6 text-base font-semibold shadow-lg transition-all hover:shadow-xl hover:scale-105 focus-visible:ring-4 focus-visible:ring-ring/35 focus-visible:ring-offset-2"
              >
                <Link href="/upload">
                  <CloudUpload className="mr-2 h-5 w-5" />
                  Upload Documents
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="rounded-full px-6 py-6 text-base font-medium"
              >
                <Link href="/search">Explore Search</Link>
              </Button>
            </div>
          </div>
        </PageHeader>
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 pb-6 sm:pb-8 flex">
        <ScrollArea className="h-[calc(100vh-12rem)] rounded-xl">
          <div className="mx-auto max-w-6xl px-4 py-6">
            <motion.div className="grid gap-6 md:grid-cols-3" {...staggeredListMotion}>
          {workflow.map(({ title, description, icon: Icon }) => (
            <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
              <Card className="card-surface h-full min-h-[180px] cursor-pointer group">
                <CardHeader className="pb-4">
                  <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary group-hover:from-primary/20 group-hover:to-primary/10 transition-colors">
                    <Icon className="h-6 w-6" strokeWidth={2.2} />
                  </div>
                  <CardTitle className="text-xl font-semibold text-foreground mt-3">{title}</CardTitle>
                </CardHeader>
                <CardContent className="text-base leading-relaxed text-muted-foreground">
                  {description}
                </CardContent>
              </Card>
            </motion.div>
          ))}
            </motion.div>
          </div>
        </ScrollArea>
      </motion.section>
    </motion.div>
  );
}
