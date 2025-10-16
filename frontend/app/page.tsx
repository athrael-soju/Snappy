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
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

const primaryFeatures = [
  {
    title: "Upload & Index",
    description: "Drop documents and let ColPali's vision AI understand both text and layout.",
    href: "/upload",
    icon: Upload,
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    title: "Search Naturally",
    description: "Ask questions in plain language and get precise, context-aware results.",
    href: "/search",
    icon: Search,
    gradient: "from-purple-500 to-pink-500",
  },
  {
    title: "Chat & Discover",
    description: "Have conversations with your documents powered by visual understanding.",
    href: "/chat",
    icon: MessageSquare,
    gradient: "from-green-500 to-emerald-500",
  },
]

const secondaryLinks = [
  { title: "Configuration", href: "/configuration", icon: Settings },
  { title: "Maintenance", href: "/maintenance", icon: Wrench },
  { title: "About", href: "/about", icon: Info },
]

export default function Home() {
  return (
    <div className="relative flex min-h-full flex-col justify-between overflow-hidden">
      {/* Hero Content - Full viewport utilization */}
      <div className="flex flex-1 flex-col justify-center px-4 py-4 text-center sm:px-6 lg:px-8">
        <div className="mx-auto w-full max-w-6xl space-y-8">
          {/* Badge */}
          <Badge 
            variant="outline" 
            className="border-primary/30 bg-primary/5 px-4 py-1.5 text-sm font-medium backdrop-blur-sm"
          >
            <Sparkles className="mr-2 h-3.5 w-3.5" />
            Powered by ColPali Vision AI
          </Badge>
          
          {/* Heading */}
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
              Vision-First
            </span>
            <br />
            <span className="bg-gradient-to-r from-primary via-purple-500 to-primary bg-clip-text text-transparent">
              Document Intelligence
            </span>
          </h1>
          
          {/* Description */}
          <p className="mx-auto max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            Search and chat with your documents using natural language. 
            Advanced visual AI understands context, not just keywords.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Button 
              asChild 
              size="lg"
              className="group h-12 gap-2 rounded-full px-6 text-base shadow-xl shadow-primary/25 transition-all hover:shadow-2xl hover:shadow-primary/30"
            >
              <Link href="/upload">
                <Upload className="h-5 w-5" />
                Get Started
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button 
              asChild 
              size="lg"
              variant="outline" 
              className="h-12 gap-2 rounded-full border-2 bg-background/50 px-6 text-base backdrop-blur-sm transition-all hover:bg-background"
            >
              <Link href="/chat">
                <MessageSquare className="h-5 w-5" />
                Try Chat
              </Link>
            </Button>
          </div>

          {/* Core Features Section */}
          <div className="pt-2">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-muted px-4 py-1.5 text-sm font-medium">
              <Zap className="h-4 w-4 text-primary" />
              Core Features
            </div>

            {/* Feature Cards */}
            <div className="grid gap-4 md:grid-cols-3">
              {primaryFeatures.map((feature, index) => (
                <Link 
                  key={feature.href}
                  href={feature.href}
                  className="group relative overflow-hidden rounded-2xl border border-border/50 bg-card/50 p-5 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-xl hover:shadow-primary/10"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 transition-opacity group-hover:opacity-5`} />
                  
                  <div className="relative flex items-start gap-3">
                    <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${feature.gradient} shadow-lg`}>
                      <feature.icon className="h-6 w-6 text-primary-foreground" />
                    </div>
                    
                    <div className="flex-1 text-left">
                      <h3 className="mb-1.5 text-base font-bold">{feature.title}</h3>
                      <p className="mb-2 text-sm leading-relaxed text-muted-foreground">
                        {feature.description}
                      </p>
                      <div className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                        Explore
                        <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-2" />
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {/* Secondary Links */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              {secondaryLinks.map((link) => (
                <Button
                  key={link.href}
                  asChild
                  variant="ghost"
                  size="default"
                  className="gap-2 rounded-full px-4"
                >
                  <Link href={link.href}>
                    <link.icon className="h-4 w-4" />
                    {link.title}
                  </Link>
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
