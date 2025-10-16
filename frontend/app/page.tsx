"use client"

import Link from "next/link"
import { 
  ArrowRight, 
  Upload, 
  Search, 
  MessageSquare, 
  Settings, 
  Wrench,
  Info,
  Sparkles,
  Zap,
  Eye
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const features = [
  {
    title: "Upload Documents",
    description: "Drop PDFs and images to index with ColPali's vision-first embeddings.",
    href: "/upload",
    icon: Upload,
    color: "text-blue-500",
  },
  {
    title: "Semantic Search",
    description: "Query your documents with natural language and get precise visual results.",
    href: "/search",
    icon: Search,
    color: "text-purple-500",
  },
  {
    title: "Chat Interface",
    description: "Ask questions and get conversational answers grounded in your documents.",
    href: "/chat",
    icon: MessageSquare,
    color: "text-green-500",
  },
  {
    title: "Configuration",
    description: "Fine-tune API settings, embedding parameters, and model configurations.",
    href: "/configuration",
    icon: Settings,
    color: "text-orange-500",
  },
  {
    title: "Maintenance",
    description: "Monitor system health, manage indexes, and perform maintenance tasks.",
    href: "/maintenance",
    icon: Wrench,
    color: "text-red-500",
  },
  {
    title: "About",
    description: "Learn about the FastAPI, Next.js, and ColPali stack powering Snappy.",
    href: "/about",
    icon: Info,
    color: "text-cyan-500",
  },
]

const highlights = [
  {
    icon: Sparkles,
    title: "Vision-First Retrieval",
    description: "ColPali embeddings capture both text and visual layout for accurate results.",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Optimized indexing and retrieval pipelines for instant search responses.",
  },
  {
    icon: Eye,
    title: "Context-Aware",
    description: "Understand document structure and context, not just keywords.",
  },
]

export default function Home() {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <section className="mb-16 text-center">
        <Badge variant="outline" className="mb-5 border-primary/50 px-4 py-1.5 text-base text-primary">
          Powered by ColPali
        </Badge>
        <h1 className="mb-5 text-5xl font-bold tracking-tight text-foreground sm:text-6xl md:text-7xl">
          Welcome to{" "}
          <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Snappy!
          </span>
        </h1>
        <p className="mx-auto mb-10 max-w-2xl text-xl text-muted-foreground sm:text-2xl">
          Your friendly vision retrieval buddy. Upload documents, search with natural language, 
          and chat with your content—all powered by cutting-edge visual embeddings.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Button asChild size="lg" className="gap-2.5 rounded-full px-6 py-6 text-base shadow-lg">
            <Link href="/upload">
              <Upload className="h-5 w-5" />
              Start Uploading
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="gap-2.5 rounded-full px-6 py-6 text-base">
            <Link href="/chat">
              <MessageSquare className="h-5 w-5" />
              Try Chat
            </Link>
          </Button>
        </div>
      </section>

      {/* Highlights */}
      <section className="mb-16">
        <div className="grid gap-8 md:grid-cols-3">
          {highlights.map((highlight) => (
            <Card key={highlight.title} className="border-border/50 bg-card/50 backdrop-blur">
              <CardContent className="pt-8">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                  <highlight.icon className="h-7 w-7 text-primary" />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-foreground">
                  {highlight.title}
                </h3>
                <p className="text-base leading-relaxed text-muted-foreground">
                  {highlight.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="mb-16">
        <div className="mb-8 text-center">
          <h2 className="mb-3 text-4xl font-bold tracking-tight text-foreground">
            Everything You Need
          </h2>
          <p className="text-lg text-muted-foreground">
            Explore all the features that make Snappy your go-to retrieval tool
          </p>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card 
              key={feature.href} 
              className="group border-border/50 transition-all hover:border-primary/50 hover:shadow-lg"
            >
              <CardHeader className="space-y-3">
                <div className="mb-2 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary/5">
                  <feature.icon className={`h-7 w-7 ${feature.color}`} />
                </div>
                <CardTitle className="text-2xl">{feature.title}</CardTitle>
                <CardDescription className="text-base">{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  asChild 
                  variant="ghost" 
                  size="sm" 
                  className="gap-2 px-0 text-base text-primary hover:bg-transparent hover:text-primary"
                >
                  <Link href={feature.href}>
                    Explore
                    <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Quick Start */}
      <section>
        <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader>
            <CardTitle className="text-3xl">Ready to Get Started?</CardTitle>
            <CardDescription className="text-lg">
              Begin your journey with Snappy in three simple steps
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-start gap-5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-base font-bold text-primary-foreground">
                1
              </div>
              <div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">Upload Your Documents</h3>
                <p className="text-base leading-relaxed text-muted-foreground">
                  Add PDFs, images, or other visual documents to build your knowledge base.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-base font-bold text-primary-foreground">
                2
              </div>
              <div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">Search & Discover</h3>
                <p className="text-base leading-relaxed text-muted-foreground">
                  Use natural language queries to find exactly what you're looking for.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-base font-bold text-primary-foreground">
                3
              </div>
              <div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">Chat & Interact</h3>
                <p className="text-base leading-relaxed text-muted-foreground">
                  Ask questions and get intelligent answers based on your documents.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
