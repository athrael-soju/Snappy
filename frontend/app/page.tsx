"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Upload, MessageSquare, Zap, Shield, Sparkles, ArrowRight, Eye, Brain, CloudUpload, Database } from "lucide-react";
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
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="text-center py-16 sm:py-24 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-purple-50/30 to-cyan-50/50 rounded-3xl" />
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
            <Badge variant="secondary" className="mb-4 px-4 py-2 bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 border-blue-200">
              <Sparkles className="w-4 h-4 mr-2" />
              Powered by Vision Language Models
            </Badge>
          </div>
          
          <h1 className="text-5xl sm:text-7xl font-bold mb-8">
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
              FastAPI / Next.js / ColPali Template
            </span>
          </h1>
          
          <p className="text-xl sm:text-2xl text-muted-foreground mb-4 max-w-3xl mx-auto leading-relaxed">
            Revolutionary document intelligence platform that understands your visual content
          </p>
          <p className="text-lg text-muted-foreground mb-12 max-w-2xl mx-auto">
            Upload documents, search using natural language, and chat with AI - all grounded by intelligent visual understanding
          </p>
          
          {/* Single primary CTA */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button 
              asChild 
              size="lg" 
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 h-14 px-8 text-lg font-semibold shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"
            >
              <Link href="/upload">
                <CloudUpload className="mr-3 h-6 w-6" />
                Start with Your Documents
                <ArrowRight className="ml-3 h-5 w-5" />
              </Link>
            </Button>
            
            <div className="text-sm text-muted-foreground">
              or
              <Link href="/search" className="ml-2 text-blue-600 hover:text-blue-700 font-medium hover:underline">
                explore with search →
              </Link>
            </div>
          </div>
          
          {/* Quick workflow preview */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex justify-center items-center gap-8 text-sm text-muted-foreground"
          >
            {workflow.map((step, idx) => {
              const StepIcon = step.icon;
              return (
                <div key={idx} className="flex items-center gap-2">
                  <div className={`p-2 rounded-full bg-white border-2 ${step.color.replace('text-', 'border-').replace('-600', '-200')}`}>
                    <StepIcon className={`w-4 h-4 ${step.color}`} />
                  </div>
                  <div className="text-left">
                    <div className="font-medium text-foreground">{step.title}</div>
                    <div className="text-xs">{step.description}</div>
                  </div>
                  {idx < workflow.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-muted-foreground/50 ml-4" />
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
