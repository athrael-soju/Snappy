"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
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
    <motion.div {...defaultPageMotion} className="page-shell page-section flex flex-col min-h-0 flex-1">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center">
        <PageHeader
          title="FastAPI / Next.js / ColPali Template"
          description="This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the boilerplate."
          icon={Sparkles}
          badge={<Badge className="rounded-full text-sm">v0.0.4</Badge>}
        >
          <div className="flex flex-col items-center gap-6">
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <Button asChild size="lg" className="primary-gradient rounded-full px-8 py-6 text-base shadow-xl">
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
                className="rounded-full border-border/60 bg-card/70 px-6 py-5 text-foreground transition hover:border-border hover:bg-card/80"
              >
                <Link href="/search">Explore search</Link>
              </Button>
            </div>
          </div>
        </PageHeader>
      </motion.section>

      <div className="flex-1 min-h-0 flex flex-col pb-10">
        <section className="space-y-8">
          <motion.div className="grid gap-6 md:grid-cols-3" {...staggeredListMotion}>
            {workflow.map(({ title, description, icon: Icon }) => (
              <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
                <Card className="card-surface h-full">
                  <CardHeader className="flex flex-row items-center gap-3 border-b border-border/40 pb-4">
                    <div className="rounded-2xl border border-border/40 bg-card/70 p-3 text-primary shadow-inner">
                      <Icon className="h-5 w-5 text-current" />
                    </div>
                    <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4 text-sm leading-relaxed text-muted-foreground/90">
                    {description}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </section>
      </div>
    </motion.div>
  );
}
