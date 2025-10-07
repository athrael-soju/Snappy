"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles, FileStack } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass-panel";
import { FeatureCard } from "@/components/ui/feature-card";

const workflow = [
  {
    title: "Upload",
    description: "Drag & drop your documents for ingestion",
    icon: CloudUpload,
    href: "/upload",
  },
  {
    title: "Process",
    description: "ColPali extracts visual embeddings automatically",
    icon: Database,
    href: "/maintenance?section=configuration",
  },
  {
    title: "Search & Chat",
    description: "Ask questions or browse visual results instantly",
    icon: Brain,
    href: "/search",
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
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 pb-6 sm:pb-8 flex">
        <ScrollArea className="h-[calc(100vh-12rem)] rounded-xl">
          <div className="mx-auto max-w-6xl px-4 py-6">
            <GlassPanel className="p-8">
              {/* Hero copy on the panel */}
              <div className="flex flex-col items-center text-center gap-6 mb-8">
                <p className="text-base text-muted-foreground max-w-2xl leading-relaxed">
                  Spin up document ingestion, visual search, and AI chat in minutes with this production-ready template.
                </p>
                
                {/* Primary CTA above the grid */}
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

              {/* 3-card grid */}
              <motion.div className="grid gap-6 md:grid-cols-3" {...staggeredListMotion}>
                {workflow.map(({ title, description, icon, href }) => (
                  <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
                    <Link 
                      href={href}
                      className="block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-2xl"
                    >
                      <FeatureCard
                        icon={icon}
                        title={title}
                        description={description}
                      />
                    </Link>
                  </motion.div>
                ))}
              </motion.div>
            </GlassPanel>
          </div>
        </ScrollArea>
      </motion.section>
    </motion.div>
  );
}
