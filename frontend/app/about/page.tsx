"use client";

import { 
  Sparkles, 
  FileText, 
  Search, 
  Settings, 
  Wrench,
  MessageSquare,
  Database,
  Code2,
  Zap,
  Shield,
  Layers,
  Cpu
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: FileText,
    title: "Document Ingestion",
    description: "Upload files to the backend, trigger indexing, and stream progress through server-sent events.",
    color: "from-blue-500 to-cyan-500"
  },
  {
    icon: Search,
    title: "Vector Search",
    description: "Query the vector store using natural language and find the most relevant document matches.",
    color: "from-purple-500 to-pink-500"
  },
  {
    icon: MessageSquare,
    title: "Conversational Chat",
    description: "Jump between keyword retrieval and conversational answers using the same vector store.",
    color: "from-green-500 to-emerald-500"
  },
  {
    icon: Settings,
    title: "Configuration",
    description: "Edit backend settings directly with inputs that mirror the OpenAPI schema.",
    color: "from-orange-500 to-amber-500"
  },
  {
    icon: Wrench,
    title: "System Maintenance",
    description: "Monitor storage status, reset data, and run maintenance operations manually.",
    color: "from-red-500 to-rose-500"
  }
];

const technologies = [
  { icon: Code2, name: "FastAPI", description: "Backend with background workers for indexing and health checks" },
  { icon: Database, name: "Qdrant", description: "Vector storage and similarity search" },
  { icon: Sparkles, name: "ColPali", description: "Visual document embeddings with vision AI" },
  { icon: Layers, name: "Next.js", description: "Frontend using React Server Components and App Router" },
  { icon: Shield, name: "TypeScript", description: "Type-safe development with OpenAPI code generation" },
  { icon: Cpu, name: "Docker", description: "Containerized deployment with GPU support" }
];

export default function AboutPage() {
  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-6">
          {/* Header Section */}
          <div className="shrink-0 space-y-2 text-center">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                About This
              </span>
              {" "}
              <span className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                Template
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground sm:text-sm">
              A modern full-stack template combining FastAPI, Next.js, and ColPali-powered visual embeddings for intelligent document processing.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Zap className="h-3 w-3 text-yellow-500" />
                Production Ready
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Code2 className="h-3 w-3 text-blue-500" />
                Type Safe
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Sparkles className="h-3 w-3 text-purple-500" />
                AI Powered
              </Badge>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="min-h-0 flex-1 space-y-6 overflow-y-auto">
            {/* Features Grid */}
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Key Features</h2>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {features.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <article 
                      key={feature.title}
                      className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10"
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 transition-opacity group-hover:opacity-5`} />
                      
                      <div className="relative space-y-2">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${feature.color} shadow-lg`}>
                          <Icon className="h-5 w-5 text-primary-foreground" />
                        </div>
                        <h3 className="text-sm font-bold">{feature.title}</h3>
                        <p className="text-xs leading-relaxed text-muted-foreground">
                          {feature.description}
                        </p>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>

            {/* Technologies */}
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Technology Stack</h2>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2">
                {technologies.map((tech) => {
                  const Icon = tech.icon;
                  return (
                    <article 
                      key={tech.name}
                      className="flex gap-3 rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm transition-all hover:border-primary/50"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary/20 to-primary/10">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div className="min-w-0 space-y-1">
                        <h3 className="text-sm font-bold">{tech.name}</h3>
                        <p className="text-xs text-muted-foreground">{tech.description}</p>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>

            {/* Architecture Overview */}
            <section className="rounded-xl border border-border/50 bg-card/30 p-4 backdrop-blur-sm">
              <div className="mb-3 flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">How It Works</h2>
              </div>
              
              <div className="space-y-3 text-sm leading-relaxed text-muted-foreground">
                <p>
                  This template provides a complete document intelligence system. Upload PDFs, images, or documents through the modern drag-and-drop interface. The backend processes them using ColPali&apos;s vision AI to understand both text and layout, creating rich embeddings stored in Qdrant.
                </p>
                <p>
                  Search using natural language queries or engage in conversational interactions. Both features leverage the same vector store, allowing seamless transitions between different retrieval modes. The configuration panel lets you tune backend settings in real-time, while maintenance tools help manage storage and data lifecycle.
                </p>
                <p>
                  The entire system is built with modern web standards: TypeScript for type safety, OpenAPI for API contract validation, React Server Components for optimal performance, and shadcn/ui for consistent, accessible components.
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
