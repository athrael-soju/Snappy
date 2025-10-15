"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { fadeInItemMotion, hoverLift, staggeredListMotion } from "@/lib/motion-presets";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Brain, CloudUpload, Database, Sparkles } from "lucide-react";
import { FeatureCard } from "@/components/ui/feature-card";
import { AppPage } from "@/components/layout";
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
  const headerActions = (
    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
      <Button asChild size="sm" className="shadow-sm">
        <Link href="/upload">
          <CloudUpload className="mr-2 h-4 w-4" />
          Upload
        </Link>
      </Button>
      <Button asChild variant="outline" size="sm">
        <Link href="/search">
          Explore Search
        </Link>
      </Button>
    </div>
  );

  return (
    <AppPage
      title="Home"
      description="Spin up document ingestion, visual search, and AI chat in minutes."
      actions={headerActions}
      contentClassName="stack stack-lg"
    >
      <div className="page-surface stack stack-sm items-center text-center p-6 sm:p-8">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <div className="stack-sm">
          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="text-xl font-semibold sm:text-2xl">
              FastAPI / Next.js / ColPali Template
            </span>
            <Badge className="rounded-full text-xs sm:text-sm">v0.0.5</Badge>
          </div>
          <p className="mx-auto max-w-2xl text-sm text-muted-foreground">
            This starter kit pairs a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on experience instead of plumbing.
          </p>
        </div>
      </div>

      <div className="stack stack-lg text-center">
        <p className="mx-auto max-w-3xl text-lg font-medium leading-relaxed text-foreground/90">
          Bring visual knowledge retrieval to life with prebuilt ingestion, search, and conversational experiences.
        </p>
        <p className="mx-auto max-w-2xl text-sm text-muted-foreground">
          Powered by <span className="font-semibold text-primary">ColPali</span>,{" "}
          <span className="font-semibold text-primary">Qdrant</span>, and a production-ready Next.js frontend.
        </p>
      </div>

      <motion.div
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3"
        {...staggeredListMotion}
      >
        {workflow.map(({ title, description, icon, href, badges, features }) => (
          <motion.div key={title} {...fadeInItemMotion} {...hoverLift}>
            <Link
              href={href}
              className={cn(
                "block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-2xl"
              )}
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
    </AppPage>
  );
}
