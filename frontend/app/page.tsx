"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowRight, Brain, CloudUpload, Database, Sparkles, Search } from "lucide-react";

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
    <div className="page-shell page-section flex flex-col min-h-0 flex-1">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center text-center"
      >
        <PageHeader
          title="ColPali Vision RAG Template"
          description="This starter kit combines a FastAPI backend, Qdrant vector search, and a modern Next.js interface so you can focus on the experience, not the boilerplate."
          icon={Sparkles}
        >
          <div className="flex flex-col items-center gap-6">
            <Badge className="rounded-full px-4 py-2 text-sm">v0.0.4</Badge>
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
          </div>
        </PageHeader>
      </motion.div>

      <div className="flex-1 min-h-0 flex flex-col pb-10">
        <section className="space-y-8">
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
      </div>
    </div>
  );
}
