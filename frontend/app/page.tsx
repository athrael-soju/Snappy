"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Upload,
  Search as SearchIcon,
  MessageSquare,
  Sparkles,
  Zap,
  Shield,
  Layers,
  TrendingUp,
  FileText,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.23, 1, 0.32, 1] as const },
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const workflowCards = [
  {
    title: "Upload Documents",
    description: "Drag and drop PDFs or images. Watch real-time processing with progress indicators.",
    icon: Upload,
    href: "/upload",
    gradient: "from-blue-500/10 to-cyan-500/10",
    iconColor: "text-blue-600 dark:text-blue-400",
  },
  {
    title: "Visual Search",
    description: "Find content using natural language. AI understands charts, tables, and layouts.",
    icon: SearchIcon,
    href: "/search",
    gradient: "from-purple-500/10 to-pink-500/10",
    iconColor: "text-purple-600 dark:text-purple-400",
  },
  {
    title: "AI Chat",
    description: "Ask questions about your documents. Get answers with visual citations.",
    icon: MessageSquare,
    href: "/chat",
    gradient: "from-green-500/10 to-emerald-500/10",
    iconColor: "text-green-600 dark:text-green-400",
  },
] as const;

const features = [
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Powered by ColPali and FastAPI for instant retrieval",
  },
  {
    icon: Shield,
    title: "Self-Hosted",
    description: "Complete control over your data and infrastructure",
  },
  {
    icon: Layers,
    title: "Modern Stack",
    description: "Next.js 15, React 19, and Tailwind v4",
  },
  {
    icon: TrendingUp,
    title: "Production Ready",
    description: "Built with best practices and type safety",
  },
] as const;

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b bg-gradient-to-br from-primary/5 via-primary/10 to-background">
        <div className="absolute inset-0 bg-grid-pattern opacity-5" />
        <div className="relative mx-auto max-w-7xl px-6 py-16 sm:px-8 lg:px-12 lg:py-24">
          <motion.div
            {...fadeIn}
            className="mx-auto max-w-3xl text-center"
          >
            <Badge className="mb-6 rounded-full bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary border-primary/20">
              <Sparkles className="mr-2 h-3.5 w-3.5" />
              Visual AI Retrieval Platform
            </Badge>
            <h1 className="mb-6 text-4xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
              Search Documents{" "}
              <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                Visually
              </span>
            </h1>
            <p className="mb-10 text-lg text-muted-foreground sm:text-xl">
              Snappy combines FastAPI and Next.js to create a powerful multimodal retrieval system.
              Upload documents, search with AI, and chat with your data.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
              <Button asChild size="lg" className="h-12 px-8 text-base shadow-lg shadow-primary/25">
                <Link href="/upload">
                  Get Started
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 px-8 text-base">
                <Link href="/about">
                  <FileText className="mr-2 h-5 w-5" />
                  Learn More
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Workflows Section */}
      <section className="border-b bg-background py-16 lg:py-24">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <motion.div
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="space-y-12"
          >
            <div className="text-center">
              <motion.h2
                variants={fadeIn}
                className="mb-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
              >
                Three Core Workflows
              </motion.h2>
              <motion.p
                variants={fadeIn}
                className="mx-auto max-w-2xl text-lg text-muted-foreground"
              >
                Everything you need to build visual AI applications
              </motion.p>
            </div>

            <motion.div
              variants={staggerContainer}
              className="grid gap-6 lg:grid-cols-3"
            >
              {workflowCards.map((workflow) => (
                <motion.div key={workflow.title} variants={fadeIn}>
                  <Link href={workflow.href} className="block h-full group">
                    <Card className="h-full transition-all duration-300 hover:shadow-xl hover:shadow-primary/10 hover:-translate-y-1">
                      <CardHeader>
                        <div className={cn(
                          "mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br",
                          workflow.gradient
                        )}>
                          <workflow.icon className={cn("h-7 w-7", workflow.iconColor)} />
                        </div>
                        <CardTitle className="text-xl font-semibold">{workflow.title}</CardTitle>
                        <CardDescription className="text-base">
                          {workflow.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center text-sm font-medium text-primary group-hover:gap-2 transition-all">
                          Get started
                          <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-muted/30 py-16 lg:py-24">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <motion.div
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={staggerContainer}
            className="space-y-12"
          >
            <div className="text-center">
              <motion.h2
                variants={fadeIn}
                className="mb-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
              >
                Built for Performance
              </motion.h2>
              <motion.p
                variants={fadeIn}
                className="mx-auto max-w-2xl text-lg text-muted-foreground"
              >
                A modern stack designed for speed, scalability, and developer experience
              </motion.p>
            </div>

            <motion.div
              variants={staggerContainer}
              className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4"
            >
              {features.map((feature) => (
                <motion.div key={feature.title} variants={fadeIn}>
                  <Card className="h-full border-muted bg-card/50 backdrop-blur">
                    <CardHeader className="text-center">
                      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                        <feature.icon className="h-6 w-6 text-primary" />
                      </div>
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                      <CardDescription className="text-sm">
                        {feature.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t bg-background py-16 lg:py-24">
        <div className="mx-auto max-w-4xl px-6 text-center sm:px-8 lg:px-12">
          <motion.div
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={fadeIn}
            className="space-y-8"
          >
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Ready to Get Started?
            </h2>
            <p className="text-lg text-muted-foreground">
              Upload your first document and experience the power of visual AI retrieval.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
              <Button asChild size="lg" className="h-12 px-8 text-base shadow-lg shadow-primary/25">
                <Link href="/upload">
                  <Upload className="mr-2 h-5 w-5" />
                  Upload Documents
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 px-8 text-base">
                <Link href="/search">
                  <SearchIcon className="mr-2 h-5 w-5" />
                  Try Search
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
