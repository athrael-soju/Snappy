"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Upload, Search as SearchIcon, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const heroMotion = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: "easeOut" },
};

const listMotion = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: "easeOut" },
};

const featureCards = [
  {
    title: "Bring visuals online",
    description:
      "Drop PDFs or image-heavy reports and let Snappy handle slicing, storage, and embedding.",
    icon: Upload,
    href: "/upload",
    cta: "Upload files",
  },
  {
    title: "Search what you see",
    description:
      "Combine text queries with layout awareness so charts, forms, and tables stay in context.",
    icon: SearchIcon,
    href: "/search",
    cta: "Open search",
  },
  {
    title: "Chat with screenshots",
    description:
      "Ask questions that reference visual snippets. Snappy surfaces matching pages as citations.",
    icon: MessageSquare,
    href: "/chat",
    cta: "Start chatting",
  },
] as const;

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-12 px-4 py-10 sm:px-6 lg:px-8">
      <motion.section
        {...heroMotion}
        className="flex flex-col items-start gap-6 rounded-xl border bg-card p-6 shadow-sm sm:p-10"
      >
        <Badge className="w-fit bg-primary/10 text-primary">Template: FastAPI + Next.js</Badge>
        <div className="space-y-4">
          <h1 className="text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Snappy makes visual RAG approachable.
          </h1>
          <p className="text-pretty text-base text-muted-foreground sm:text-lg">
            A friendly starter that pairs a FastAPI backend with a shadcn-powered Next.js UI.
            Simplified styles, sensible defaults, and clear docs help you focus on your product
            instead of scaffolding.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button asChild size="lg">
            <Link href="/upload">
              Ingest a document
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/search">Try the search workflow</Link>
          </Button>
        </div>
      </motion.section>

      <motion.section
        {...listMotion}
        transition={{ ...listMotion.transition, delay: 0.1 }}
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        {featureCards.map(({ title, description, icon: Icon, href, cta }) => (
          <motion.div
            key={title}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.3 }}
          >
            <Card className="h-full">
              <CardHeader className="space-y-3">
                <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-lg font-semibold">{title}</CardTitle>
              </CardHeader>
              <CardContent className="flex h-full flex-col gap-5 text-sm text-muted-foreground">
                <p>{description}</p>
                <Button asChild variant="ghost" className="mt-auto w-fit px-0">
                  <Link href={href}>
                    {cta}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.section>
    </div>
  );
}
