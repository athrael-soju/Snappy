"use client";

import Link from "next/link";
import { Button } from "@/components/ui/8bit/button";
import { Badge } from "@/components/ui/8bit/badge";
import { Sparkles, ArrowRight, Eye, Brain, CloudUpload, Database } from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    icon: Eye,
    title: "AI-Powered Visual Search",
    description: "Find documents using natural language descriptions",
    detail: "Advanced ColPali embeddings understand visual content context",
    color: "text-blue-500",
    bgColor: "from-blue-500/10 to-cyan-500/10",
    borderColor: "border-blue-200/50",
    preview: "search-preview"
  },
  {
    icon: CloudUpload,
    title: "Smart Document Processing",
    description: "Drag & drop files for instant processing",
    detail: "Automatic indexing with progress tracking and format detection",
    color: "text-green-500",
    bgColor: "from-green-500/10 to-emerald-500/10",
    borderColor: "border-green-200/50",
    preview: "upload-preview"
  },
  {
    icon: Brain,
    title: "Intelligent Chat with Citations",
    description: "Ask questions and get visual proof",
    detail: "AI responses backed by relevant document excerpts and images",
    color: "text-purple-500",
    bgColor: "from-purple-500/10 to-pink-500/10",
    borderColor: "border-purple-200/50",
    preview: "chat-preview"
  }
];

const workflow = [
  { step: 1, title: "Upload", description: "Drag & drop your documents", icon: CloudUpload, color: "text-blue-600" },
  { step: 2, title: "Process", description: "AI analyzes visual content", icon: Database, color: "text-purple-600" },
  { step: 3, title: "Search & Chat", description: "Find and discuss your documents", icon: Brain, color: "text-green-600" }
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5
    }
  }
};

export default function Home() {
  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="text-center py-12 sm:py-16 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-32 h-32 bg-blue-200/20 rounded-full blur-xl" />
          <div className="absolute top-40 right-32 w-24 h-24 bg-purple-200/20 rounded-full blur-xl" />
          <div className="absolute bottom-32 left-1/3 w-40 h-40 bg-cyan-200/20 rounded-full blur-xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-5xl mx-auto relative z-10"
        >
          <div className="mb-6">
            <Badge variant="secondary" className="mb-4 px-3 py-1 bg-gradient-to-r from-primary/10 to-accent/10 text-primary border-primary/20">
              <Sparkles className="w-4 h-4 mr-2" />
              Powered by the ColPali Vision
            </Badge>
          </div>

          <h1 className="text-4xl sm:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-primary via-accent to-ring bg-clip-text text-transparent">
              FastAPI / Next.js / ColPali
            </span>
            <br />
            <span className="bg-gradient-to-r from-primary via-accent to-ring bg-clip-text text-transparent">
              Template
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground mb-3 max-w-2xl mx-auto leading-relaxed">
            A lightweight, end-to-end template for knowledge retrieval using
            <br />ColPali
          </p>
          <p className="text-base text-muted-foreground mb-8 max-w-xl mx-auto">
            Upload documents, search using natural language, and chat with an AI assistant
          </p>

          {/* Single primary CTA */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center mb-8">
            <Button
              asChild
              size="lg"
              className="bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-6 text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 retro"
            >
              <Link href="/upload">
                Start with Your Documents
              </Link>
            </Button>

            <div className="text-sm text-muted-foreground">
              or
              <Link href="/search" className="ml-2 text-primary hover:text-primary/90 font-medium hover:underline">
                explore with search →
              </Link>
            </div>
          </div>

          {/* Quick workflow preview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex flex-col sm:flex-row justify-center items-center gap-4 sm:gap-6 text-sm text-muted-foreground"
          >
            {workflow.map((step, idx) => {
              const StepIcon = step.icon;
              return (
                <div key={idx} className="flex items-center gap-2">
                  <div className={`p-2 rounded bg-card border-2 border-border shadow-sm ${step.color}`}>
                    <StepIcon className={`w-4 h-4`} />
                  </div>
                  <div className="text-left">
                    <div className="font-medium text-foreground text-sm">{step.title}</div>
                    <div className="text-xs">{step.description}</div>
                  </div>
                  {idx < workflow.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-muted-foreground/50 ml-2 hidden sm:block" />
                  )}
                </div>
              );
            })}
          </motion.div>
        </motion.div>
      </section>
    </div>
  );
}
