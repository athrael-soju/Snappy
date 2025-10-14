"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { 
  Info, 
  Layers, 
  Server, 
  Database, 
  Brain, 
  Rocket, 
  Code, 
  Zap,
  ArrowRight,
  ExternalLink,
  Book,
  Github
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

const stackItems = [
  {
    icon: Layers,
    title: "Frontend",
    description: "Next.js 15 with React 19, Tailwind v4, and shadcn/ui components",
    technologies: ["Next.js", "React", "TypeScript", "Tailwind CSS"],
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: Server,
    title: "Backend",
    description: "FastAPI for high-performance REST endpoints with automatic OpenAPI docs",
    technologies: ["FastAPI", "Python", "Pydantic", "OpenAPI"],
    color: "from-green-500 to-emerald-500",
  },
  {
    icon: Database,
    title: "Storage",
    description: "Qdrant vector database and MinIO object storage for scalable data management",
    technologies: ["Qdrant", "MinIO", "Vector DB", "S3 Compatible"],
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: Brain,
    title: "AI Model",
    description: "ColQwen2.5 vision model for multimodal document understanding",
    technologies: ["ColPali", "Vision Language Model", "Embeddings"],
    color: "from-orange-500 to-red-500",
  },
];

const features = [
  {
    icon: Rocket,
    title: "Quick Start",
    description: "Get started in minutes with Docker Compose or local development",
  },
  {
    icon: Code,
    title: "Type Safe",
    description: "Full TypeScript support with auto-generated API client",
  },
  {
    icon: Zap,
    title: "Real-time",
    description: "Live configuration updates and instant search results",
  },
];

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-muted/30 to-background">
      {/* Hero Header */}
      <div className="relative overflow-hidden border-b bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-transparent">
        <div className="absolute inset-0 bg-grid-pattern opacity-30" />
        <div className="relative mx-auto max-w-7xl px-6 py-20 sm:px-8 lg:px-12">
          <motion.div {...fadeIn} className="mx-auto max-w-3xl text-center space-y-6">
            <div className="flex justify-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25">
                <Info className="h-10 w-10 text-white" />
              </div>
            </div>
            
            <div className="space-y-4">
              <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
                About <span className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent">Snappy</span>
              </h1>
              <p className="text-xl text-muted-foreground">
                A modern template for building visual AI retrieval applications with FastAPI and Next.js
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-4">
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                FastAPI + Next.js
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                ColQwen2.5
              </Badge>
              <Badge variant="secondary" className="px-4 py-2 text-sm">
                Open Source
              </Badge>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-12 sm:px-8 lg:px-12">
        <div className="space-y-16">
          {/* What is Snappy */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="space-y-6"
          >
            <Card className="border-2">
              <CardContent className="p-8 sm:p-12">
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold text-foreground">What is Snappy?</h2>
                  <div className="prose prose-lg dark:prose-invert max-w-none">
                    <p className="text-muted-foreground leading-relaxed">
                      Snappy is a production-ready template that helps you build visual AI retrieval applications quickly. 
                      Upload PDFs, images, or documents to enable semantic search and chat with visual citations. 
                      Everything runs locally, giving you complete control over your data and deployment.
                    </p>
                    <p className="text-muted-foreground leading-relaxed">
                      Built with modern technologies and best practices, Snappy provides a solid foundation for 
                      multimodal AI applications. Whether you're prototyping or building for production, Snappy 
                      scales from local development to cloud deployment.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.section>

          {/* Technology Stack */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="space-y-6"
          >
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-bold text-foreground">Technology Stack</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Built with cutting-edge technologies for performance, scalability, and developer experience
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              {stackItems.map((item, index) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="h-full border-2 hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${item.color} mb-4`}>
                        <item.icon className="h-7 w-7 text-white" />
                      </div>
                      <CardTitle className="text-xl">{item.title}</CardTitle>
                      <CardDescription className="text-base">
                        {item.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {item.technologies.map((tech) => (
                          <Badge key={tech} variant="outline" className="text-xs">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.section>

          {/* Features */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="space-y-6"
          >
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-bold text-foreground">Key Features</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Everything you need to build production-ready AI applications
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {features.map((feature) => (
                <Card key={feature.title} className="border-2">
                  <CardContent className="p-6 text-center space-y-4">
                    <div className="flex justify-center">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                        <feature.icon className="h-6 w-6 text-primary" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-semibold text-foreground">{feature.title}</h3>
                      <p className="text-sm text-muted-foreground">{feature.description}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </motion.section>

          {/* Quick Start */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <Card className="border-2 bg-gradient-to-br from-primary/5 to-background">
              <CardContent className="p-8 sm:p-12">
                <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h2 className="text-3xl font-bold text-foreground">Get Started</h2>
                      <p className="text-lg text-muted-foreground">
                        Three steps to start exploring your documents with AI
                      </p>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-start gap-4">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
                          1
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground">Upload Documents</h3>
                          <p className="text-sm text-muted-foreground">Drag and drop PDFs or images on the upload page</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-4">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
                          2
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground">Search Visually</h3>
                          <p className="text-sm text-muted-foreground">Use natural language to find specific pages</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-4">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
                          3
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground">Chat with AI</h3>
                          <p className="text-sm text-muted-foreground">Ask questions and get answers with visual citations</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <Button asChild size="lg" className="w-full gap-2">
                      <Link href="/upload">
                        <Rocket className="h-5 w-5" />
                        Start Uploading
                        <ArrowRight className="h-5 w-5" />
                      </Link>
                    </Button>
                    <Button asChild variant="outline" size="lg" className="w-full gap-2">
                      <Link href="/search">
                        <Book className="h-5 w-5" />
                        Explore Search
                      </Link>
                    </Button>
                    <Button asChild variant="outline" size="lg" className="w-full gap-2">
                      <Link href="https://github.com" target="_blank">
                        <Github className="h-5 w-5" />
                        View on GitHub
                        <ExternalLink className="h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.section>
        </div>
      </div>
    </div>
  );
}
