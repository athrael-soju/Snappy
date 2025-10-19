"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Upload,
  Search,
  MessageSquare,
  Settings,
  Shield,
  Sparkles,
  Cloud,
  Globe,
} from "lucide-react";

import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";

const primaryFeatures = [
  {
    title: "Upload & Index",
    description:
      "Streamline document ingress with Vultr's object storage and ColPali-powered parsing across PDFs, slides, and scans.",
    href: "/upload",
    icon: Upload,
    accent: "from-vultr-sky-blue via-vultr-light-blue to-vultr-blue",
  },
  {
    title: "Semantic Search",
    description:
      "Obtain grounded answers with cross-modal search tuned for global teams and regulatory workloads.",
    href: "/search",
    icon: Search,
    accent: "from-vultr-blue via-vultr-cobalt to-vultr-blue-60",
  },
  {
    title: "Vision Chat",
    description:
      "Collaborate in natural language with ColPali's visual reasoning to accelerate reviews, audits, and deployments.",
    href: "/chat",
    icon: MessageSquare,
    accent: "from-vultr-light-blue via-vultr-sky-blue to-white/80",
  },
] as const;

const secondaryLinks = [
  { title: "Configuration", href: "/configuration", icon: Settings },
  { title: "Maintenance", href: "/maintenance", icon: Shield },
] as const;

const stats = [
  {
    value: "32",
    unit: "regions",
    description: "Global Vultr data centers keep low latency retrieval within reach.",
    icon: Globe,
  },
  {
    value: "GPU",
    unit: "fleet",
    description: "Deploy H100, A100, and L40S clusters for inference without overprovisioning.",
    icon: Cloud,
  },
  {
    value: "99.99%",
    unit: "uptime",
    description: "The reliability your AI workflows demand with transparent SLAs.",
    icon: Shield,
  },
] as const;

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 120, damping: 16 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 24, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 120, damping: 18 },
  },
};

export default function Home() {
  return (
    <div className="relative flex min-h-0 flex-1 flex-col overflow-y-auto">
      <motion.section
        className="bg-hero-vultr text-white"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        <div className="mx-auto max-w-7xl px-6 section-spacing grid grid-cols-4 gap-6">
          <motion.div className="col-span-4 space-y-6 md:col-span-3" variants={itemVariants}>
            <Image
              src="/brand/vultr-logo-reversed.svg"
              alt="Vultr"
              width={180}
              height={60}
              priority
              className="logo-min h-12 w-auto"
            />

            <div className="space-y-4">
              <Badge variant="secondary" className="bg-white/20 text-white hover:bg-white/25">
                Powered by ColPali
              </Badge>
              <h1>Global ColPali Vision at Vultr Speed</h1>
              <p className="max-w-2xl text-white/80">
                Activate Vultr's ColPali template for rapid document intelligence. Move from ingestion to
                insight with GPU acceleration, global availability, and the blueprints trusted by enterprise
                teams.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <AppButton asChild variant="hero" size="lg" elevated>
                <Link href="/upload">
                  Deploy Workspace
                </Link>
              </AppButton>
              <AppButton
                asChild
                variant="glass"
                size="lg"
                elevated
              >
                <Link href="https://www.vultr.com/company/contact/" target="_blank" rel="noopener noreferrer">
                  Contact Sales
                </Link>
              </AppButton>
            </div>

            <motion.div className="grid gap-4 sm:grid-cols-3" variants={containerVariants}>
              {stats.map((stat) => (
                <motion.div
                  key={stat.value}
                  variants={cardVariants}
                  className="rounded-[var(--radius-card)] border border-white/15 bg-white/10 p-4 backdrop-blur-md"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-white/15">
                      <stat.icon className="h-5 w-5 text-vultr-sky-blue" />
                    </span>
                    <div>
                      <p className="text-2xl font-semibold text-white">
                        {stat.value}
                        <span className="ml-1 text-base uppercase tracking-wider text-white/70">{stat.unit}</span>
                      </p>
                      <p className="text-sm text-white/70">{stat.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>

          <motion.aside className="col-span-4 md:col-span-1" variants={itemVariants}>
            <div className="card-dark vultr-gradient-border flex h-full flex-col gap-4 p-6">
              <h3 className="text-lg font-semibold text-white">Why teams choose Vultr</h3>
              <ul className="space-y-3 text-sm text-white/80">
                <li className="flex items-start gap-3">
                  <Sparkles className="mt-0.5 h-5 w-5 text-vultr-light-blue" />
                  <span>Unified ingestion, retrieval, and chat flows aligned to Vultr's brand playbooks.</span>
                </li>
                <li className="flex items-start gap-3">
                  <Cloud className="mt-0.5 h-5 w-5 text-vultr-sky-blue" />
                  <span>GPU availability across 32 regions with predictable pricing.</span>
                </li>
                <li className="flex items-start gap-3">
                  <Shield className="mt-0.5 h-5 w-5 text-white/80" />
                  <span>Isolation-ready architecture for sovereignty and regulated workloads.</span>
                </li>
              </ul>

              <div className="mt-auto rounded-[calc(var(--radius-card)-0.5rem)] bg-white/10 p-4 text-sm text-white/75 backdrop-blur-lg">
                <p>
                  Configure multiple ColPali deployments, enforce enterprise policy, and monitor pipelines from
                  a single Vultr console.
                </p>
              </div>
            </div>
          </motion.aside>
        </div>
      </motion.section>

      <section className="bg-warm-1">
        <div className="mx-auto max-w-7xl px-6 section-spacing-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="space-y-3">
              <span className="badge badge-neutral uppercase tracking-[0.18em] text-xs">Platform Features</span>
              <h2>From ingestion to insight in minutes</h2>
              <p className="max-w-2xl text-base text-vultr-blue-20">
                Orchestrate document intelligence workflows with Vultr's design system. Use enterprise-ready
                components to maintain consistency from upload through retrieval.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <AppButton asChild variant="outline" size="sm">
                <Link href="/search">Explore Search</Link>
              </AppButton>
              <AppButton asChild variant="ghost" size="sm">
                <Link href="/maintenance">Service Status</Link>
              </AppButton>
            </div>
          </div>

          <motion.div className="mt-10 grid gap-6 md:grid-cols-3" variants={containerVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-80px" }}>
            {primaryFeatures.map((feature) => (
              <motion.div
                key={feature.href}
                variants={cardVariants}
                whileHover={{ translateY: -6 }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
              >
                <Link
                  href={feature.href}
                  className="group card h-full overflow-hidden p-6 transition-transform duration-200 hover:shadow-xl"
                >
                  <div
                    className={`inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.accent} text-white shadow-[var(--shadow-soft)]`}
                  >
                    <feature.icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold text-vultr-navy">{feature.title}</h3>
                  <p className="mt-2 text-sm text-vultr-blue-20">{feature.description}</p>
                  <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-vultr-blue">
                    Dive In
                    <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1.5" />
                  </span>
                </Link>
              </motion.div>
            ))}
          </motion.div>

          <motion.div className="mt-10 flex flex-wrap items-center gap-3" variants={containerVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-80px" }}>
            {secondaryLinks.map((link) => (
              <motion.div key={link.href} variants={itemVariants}>
                <AppButton asChild variant="ghost" size="sm">
                  <Link href={link.href} className="flex items-center gap-2">
                    <link.icon className="h-4 w-4" />
                    {link.title}
                  </Link>
                </AppButton>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    </div>
  );
}
