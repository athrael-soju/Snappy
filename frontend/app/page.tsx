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
              ColPali UI
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

      {/* Features Section */}
      <section className="relative">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center mb-16"
        >
          <motion.div variants={itemVariants} className="mb-6">
            <Badge variant="outline" className="px-4 py-2 text-sm">
              <Zap className="w-4 h-4 mr-2 text-yellow-500" />
              Core Capabilities
            </Badge>
          </motion.div>
          <motion.h2 
            variants={itemVariants}
            className="text-4xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
          >
            Intelligent Document Processing
          </motion.h2>
          <motion.p 
            variants={itemVariants}
            className="text-muted-foreground text-xl max-w-3xl mx-auto leading-relaxed"
          >
            Experience the future of document interaction with AI-powered visual understanding that goes beyond simple text search
          </motion.p>
        </motion.div>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 lg:grid-cols-3 gap-8"
        >
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div key={index} variants={itemVariants}>
                <Card className={`h-full group hover:shadow-2xl transition-all duration-500 hover:-translate-y-3 border-2 ${feature.borderColor} bg-gradient-to-br ${feature.bgColor} relative overflow-hidden`}>
                  {/* Background pattern */}
                  <div className="absolute inset-0 bg-grid-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  
                  <CardHeader className="pb-6 relative z-10">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`inline-flex w-14 h-14 items-center justify-center rounded-2xl ${feature.color} bg-white/80 border-2 ${feature.borderColor} mb-4 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg`}>
                        <Icon className="w-7 h-7" />
                      </div>
                      <Badge variant="outline" className="text-xs">
                        #{index + 1}
                      </Badge>
                    </div>
                    <CardTitle className={`text-xl font-bold ${feature.color} group-hover:scale-105 transition-transform duration-300 origin-left`}>
                      {feature.title}
                    </CardTitle>
                    <CardDescription className="text-base leading-relaxed text-muted-foreground">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="relative z-10">
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {feature.detail}
                      </p>
                      
                      {/* Feature preview mockup */}
                      <div className="mt-4 p-3 bg-white/60 rounded-lg border border-white/40 group-hover:bg-white/80 transition-colors duration-300">
                        {feature.preview === 'search-preview' && (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Search className="w-3 h-3" />
                              <span>"Find charts with financial data"</span>
                            </div>
                            <div className="grid grid-cols-3 gap-1">
                              {[1,2,3].map(i => (
                                <div key={i} className="h-8 bg-gradient-to-r from-blue-100 to-blue-200 rounded border" />
                              ))}
                            </div>
                          </div>
                        )}
                        {feature.preview === 'upload-preview' && (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <CloudUpload className="w-3 h-3" />
                              <span>3 files processing...</span>
                            </div>
                            <div className="h-2 bg-gradient-to-r from-green-200 to-green-400 rounded-full" />
                          </div>
                        )}
                        {feature.preview === 'chat-preview' && (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Brain className="w-3 h-3" />
                              <span>AI analyzing documents...</span>
                            </div>
                            <div className="flex gap-1">
                              {[1,2,3,4].map(i => (
                                <div key={i} className="w-4 h-4 bg-gradient-to-r from-purple-100 to-purple-200 rounded border" />
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* Value Proposition Section */}
      <motion.section 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="relative overflow-hidden"
      >
        {/* Background with gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-purple-600/5 to-cyan-600/5 rounded-3xl" />
        <div className="absolute inset-0 bg-gradient-to-r from-blue-50/50 via-purple-50/30 to-cyan-50/50 rounded-3xl" />
        
        <div className="relative z-10 p-12">
          <div className="text-center space-y-8">
            <div className="space-y-4">
              <Badge variant="secondary" className="px-6 py-3 bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-800 border-yellow-200">
                <Zap className="w-5 h-5 mr-2" />
                Why Choose ColPali UI?
              </Badge>
              
              <h3 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Beyond Traditional Document Search
              </h3>
              
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                While others search just text, we understand your documents visually - charts, diagrams, layouts, and context
              </p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mt-12">
              {[
                { 
                  label: "Visual Intelligence", 
                  icon: Eye, 
                  desc: "Understands charts, diagrams & layouts",
                  color: "text-blue-600",
                  bgColor: "bg-blue-500/10"
                },
                { 
                  label: "Lightning Fast", 
                  icon: Zap, 
                  desc: "Instant search & real-time responses",
                  color: "text-yellow-600",
                  bgColor: "bg-yellow-500/10"
                },
                { 
                  label: "Privacy First", 
                  icon: Shield, 
                  desc: "Your documents stay secure",
                  color: "text-green-600",
                  bgColor: "bg-green-500/10"
                },
                { 
                  label: "AI Powered", 
                  icon: Sparkles, 
                  desc: "Latest vision language models",
                  color: "text-purple-600",
                  bgColor: "bg-purple-500/10"
                }
              ].map((stat, i) => {
                const StatIcon = stat.icon;
                return (
                  <motion.div 
                    key={i} 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.6 + i * 0.1 }}
                    className="text-center space-y-4 group"
                  >
                    <div className={`inline-flex w-16 h-16 items-center justify-center rounded-2xl ${stat.bgColor} ${stat.color} mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg border-2 border-white/50`}>
                      <StatIcon className="w-8 h-8" />
                    </div>
                    <div>
                      <div className="font-bold text-lg text-foreground mb-1">{stat.label}</div>
                      <div className="text-sm text-muted-foreground leading-relaxed">{stat.desc}</div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
            
            {/* Call to action */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 1 }}
              className="mt-12 pt-8 border-t border-muted-foreground/10"
            >
              <p className="text-lg text-muted-foreground mb-6">
                Ready to revolutionize how you work with documents?
              </p>
              <Button 
                asChild 
                size="lg" 
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 h-12 px-8 font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <Link href="/upload">
                  <CloudUpload className="mr-2 h-5 w-5" />
                  Upload Your First Document
                </Link>
              </Button>
            </motion.div>
          </div>
        </div>
      </motion.section>
    </div>
  );
}
