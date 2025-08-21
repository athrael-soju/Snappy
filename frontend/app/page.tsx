"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Upload, MessageSquare, Zap, Shield, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    icon: Search,
    title: "Fast Visual Search",
    description: "Retrieve relevant images and pages instantly",
    detail: "Powered by Qdrant and ColPali embeddings",
    color: "text-blue-500"
  },
  {
    icon: Upload,
    title: "Simple Uploads",
    description: "Batch upload files via MinIO storage",
    detail: "Support for multiple file formats",
    color: "text-green-500"
  },
  {
    icon: MessageSquare,
    title: "Chat Grounded by Images",
    description: "Ask questions and see supporting visuals",
    detail: "Image citations with labels and scores",
    color: "text-purple-500"
  }
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
      <section className="text-center py-16 sm:py-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <h1 className="text-4xl sm:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
              ColPali UI
            </span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Document search and AI chat using vision language models. Upload, search, and chat with your documents.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Button asChild size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
              <Link href="/upload">
                <Upload className="mr-2 h-5 w-5" />
                Get Started
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/search">
                <Search className="mr-2 h-5 w-5" />
                Try Search
              </Link>
            </Button>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section>
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="text-center mb-12"
        >
          <motion.h2 
            variants={itemVariants}
            className="text-3xl font-bold mb-4"
          >
            Key Features
          </motion.h2>
          <motion.p 
            variants={itemVariants}
            className="text-muted-foreground text-lg max-w-2xl mx-auto"
          >
            Visual document understanding made simple
          </motion.p>
        </motion.div>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div key={index} variants={itemVariants}>
                <Card className="h-full group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 border-2 hover:border-accent">
                  <CardHeader className="pb-4">
                    <div className={`inline-flex w-12 h-12 items-center justify-center rounded-xl ${feature.color} bg-accent/10 mb-4 group-hover:scale-110 transition-transform`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <CardTitle className="text-xl group-hover:text-foreground/90 transition-colors">
                      {feature.title}
                    </CardTitle>
                    <CardDescription className="text-base">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {feature.detail}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* Stats Section */}
      <motion.section 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
        className="bg-gradient-to-r from-accent/30 to-muted/30 rounded-2xl p-8"
      >
        <div className="text-center space-y-6">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Zap className="w-6 h-6 text-yellow-500" />
            <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">AI Powered</span>
          </div>
          
          <h3 className="text-2xl font-bold">
            Smart Document Processing
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-8">
            {[
              { label: "Fast", icon: Zap, desc: "Quick results" },
              { label: "Accurate", icon: Search, desc: "Precise search" },
              { label: "Secure", icon: Shield, desc: "Private data" },
              { label: "Modern", icon: Sparkles, desc: "Latest AI" }
            ].map((stat, i) => {
              const StatIcon = stat.icon;
              return (
                <div key={i} className="text-center space-y-2">
                  <div className="inline-flex w-12 h-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-2">
                    <StatIcon className="w-5 h-5" />
                  </div>
                  <div className="font-semibold">{stat.label}</div>
                  <div className="text-sm text-muted-foreground">{stat.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </motion.section>
    </div>
  );
}
