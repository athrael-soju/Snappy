"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { FeatureCard } from "@/components/ui/feature-card";
import type { GlassDepth } from "@/components/ui/glass-panel";

const workflow: Array<{
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
  badges: string[];
  features: string[];
  depth: GlassDepth;
}> = [
  {
    title: "Upload & Ingest",
    description: "Effortlessly bring your documents into the system with intelligent processing",
    icon: CloudUpload,
    href: "/upload",
    badges: ["PDF", "Images", "Multi-page"],
    features: [
      "Drag-and-drop interface with batch upload",
      "Automatic format detection and validation",
      "Real-time progress tracking and status",
      "Secure storage with metadata extraction",
    ],
    depth: "overlay",
  },
  {
    title: "Visual Embeddings",
    description: "ColPali transforms documents into searchable visual representations",
    icon: Database,
    href: "/maintenance?section=configuration",
    badges: ["AI-Powered", "Qdrant", "GPU Ready"],
    features: [
      "Vision-language model for deep understanding",
      "Page-level embeddings for precise retrieval",
      "Vector database with similarity search",
      "Configurable processing pipeline",
    ],
    depth: "surface",
  },
  {
    title: "Search & Chat",
    description: "Interact naturally with your documents using AI-powered search and conversation",
    icon: Brain,
    href: "/search",
    badges: ["RAG", "Multi-modal", "Real-time"],
    features: [
      "Natural language queries with context awareness",
      "Visual similarity search across documents",
      "AI chat with document citations and sources",
      "Instant results with relevance scoring",
    ],
    depth: "background",
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
            {/* Hero copy */}
            <div className="flex flex-col items-center text-center gap-6 mb-8">
              <div className="space-y-3 max-w-3xl">
                <p className="text-lg text-foreground/90 leading-relaxed font-medium">
                  Spin up document ingestion, visual search, and AI chat in minutes with this production-ready template.
                </p>
                <p className="text-sm text-foreground/70 font-medium">
                  Powered by <span className="font-semibold text-primary hover:text-primary/80 transition-colors">ColPali</span>, <span className="font-semibold text-primary hover:text-primary/80 transition-colors">Qdrant</span>, and modern web technologies
                </p>
              </div>
              
              {/* Primary CTA above the grid */}
              <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4">
                <Button
                  asChild
                  size="lg"
                  className="primary-gradient motion-cta rounded-full px-8 py-6 text-base font-semibold focus-visible:ring-4 focus-visible:ring-ring/35 focus-visible:ring-offset-2"
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
            <motion.div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" {...staggeredListMotion}>
              {workflow.map(({ title, description, icon, href, badges, features, depth }) => (
                <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
                  <Link
                    href={href}
                    className="block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-2xl"
                  >
                    <FeatureCard
                      icon={icon}
                      title={title}
                      description={description}
                      badges={badges}
                      features={features}
                      glass
                      glassDepth={depth}
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
