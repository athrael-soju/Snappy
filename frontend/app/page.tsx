"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles } from "lucide-react";
import { FeatureCard } from "@/components/ui/feature-card";
import { GlassPanel } from "@/components/ui/glass-panel";
import { cn } from "@/lib/utils";

const workflow = [
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
  },
  {
    title: "Visual Embeddings",
    description: "ColPali transforms documents into searchable visual representations",
    icon: Database,
    href: "/configuration",
    badges: ["AI-Powered", "Qdrant", "GPU Ready"],
    features: [
      "Vision-language model for deep understanding",
      "Page-level embeddings for precise retrieval",
      "Vector database with similarity search",
      "Configurable processing pipeline",
    ],
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
  },
];

export default function Home() {
  return (
    <motion.div {...defaultPageMotion} className="mx-auto w-full max-w-[1240px] h-full px-4 sm:px-6 lg:px-8">
      {/* Page stack */}
      <div className="flex h-full flex-col gap-4 sm:gap-6 py-4 sm:py-6">
        {/* Header card */}
        <motion.div variants={sectionVariants} className="flex-shrink-0">
          <GlassPanel className="p-4 sm:p-6">
            <div className="flex flex-col items-center text-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="flex items-center justify-center gap-2 mb-2">
                  <h1 className="text-2xl font-semibold">FastAPI / Next.js / ColPali Template</h1>
                  <Badge className="rounded-full text-sm">v0.0.5</Badge>
                </div>
                <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
                  This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the configuration
                </p>
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* Content section - scrollable */}
        <motion.div variants={sectionVariants} className="flex-1 min-h-0">
          <div 
            className="h-full overflow-y-auto px-2 sm:px-4 py-4 sm:py-6"
            style={{ overscrollBehavior: 'contain', scrollbarGutter: 'stable' }}
          >
            {/* Hero copy */}
            <div className="flex flex-col items-center text-center gap-4 sm:gap-6 mb-6 sm:mb-8">
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
            <motion.div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" {...staggeredListMotion}>
              {workflow.map(({ title, description, icon, href, badges, features }) => (
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
                    />
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
