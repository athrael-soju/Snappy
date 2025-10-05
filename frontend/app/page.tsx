"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles, MessageSquare, Search } from "lucide-react";

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
    <main className="page-shell page-section space-y-16">
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center text-center gap-8"
      >
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-foreground max-w-3xl">
          ColPali Vision RAG Template <Badge className="ml-2">v0.0.4</Badge>
        </h1>
        <p className="text-muted-foreground max-w-2xl leading-relaxed">
          This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the boilerplate.
        </p>
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Button asChild size="lg" className="primary-gradient rounded-full px-8 py-6 text-base shadow-lg">
            <Link href="/upload">
              <CloudUpload className="mr-3 h-5 w-5" />
              Upload your documents
              <ArrowRight className="ml-3 h-5 w-5" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="rounded-full px-6 py-5">
            <Link href="/search">Explore search</Link>
          </Button>
        </div>
      </motion.section>

      <section className="page-section">
        <div className="grid gap-6 md:grid-cols-3">
          {workflow.map(({ title, description, icon: Icon }) => (
            <Card key={title} className="card-surface h-full">
              <CardHeader className="flex flex-row items-center gap-3">
                <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-lg font-semibold">{title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground leading-relaxed">
                {description}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
