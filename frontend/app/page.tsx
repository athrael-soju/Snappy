"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles } from "lucide-react";
import { FeatureCard } from "@/components/ui/feature-card";

const workflow = [
  {
    title: "Load Your Library",
    description: "Drop PDFs, decks, and scans. Snappy neatly ingests every page.",
    icon: CloudUpload,
    href: "/upload",
    badges: ["Batch Upload", "Auto-tagged"],
    features: [
      "Drag, drop, and watch progress in real time",
      "Smart validation keeps your library tidy",
      "Friendly status to show what's ready",
    ],
  },
  {
    title: "See Everything",
    description: "Visual embeddings unlock layout-aware search you can trust.",
    icon: Database,
    href: "/maintenance?section=configuration",
    badges: ["Vector Search", "GPU Friendly"],
    features: [
      "Vision-first indexing tuned for documents",
      "Metadata tools to shape your workspace",
      "Snappy health checks keep pipelines fresh",
    ],
  },
  {
    title: "Find & Chat",
    description: "Ask a question, get grounded answers with cited snapshots.",
    icon: Brain,
    href: "/search",
    badges: ["Chat Ready", "Citations"],
    features: [
      "Natural language search across every page",
      "Instant previews so you trust the matches",
      "Conversational chat that remembers context",
    ],
  },
];

export default function Home() {
  return (
    <motion.div {...defaultPageMotion} className="page-shell flex min-h-0 flex-1 flex-col">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
        <PageHeader
          title="Snappy"
          icon={Sparkles}
          badge={<Badge className="rounded-full text-sm px-3 py-1">Vision Retrieval Buddy</Badge>}
          tooltip="Snappy keeps visual documents searchable and friendly so your team can share answers faster."
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 pb-6 sm:pb-8 flex">
        <ScrollArea className="h-[calc(100vh-12rem)] rounded-xl">
          <div className="mx-auto max-w-6xl px-4 py-6">
            {/* Hero copy */}
            <div className="flex flex-col items-center text-center gap-6 mb-8">
              <div className="space-y-3 max-w-2xl">
                <p className="text-lg text-foreground/90 leading-relaxed font-semibold">
                  Meet your new visual knowledge buddy. Snappy turns slides, scans, and PDFs into answers you can see.
                </p>
                <p className="text-sm text-muted-foreground">
                  Upload once, retrieve instantly, and keep conversations grounded in citations that pop.
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
                    Add Documents
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="rounded-full px-6 py-6 text-base font-medium"
                >
                  <Link href="/search">Try Retrieval</Link>
                </Button>
              </div>
            </div>

            {/* 3-card grid */}
            <motion.div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" {...staggeredListMotion}>
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
        </ScrollArea>
      </motion.section>
    </motion.div>
  );
}
