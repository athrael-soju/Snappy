"use client";

import Link from "next/link";
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

const productCards = [
  {
    title: "Upload & Index",
    description:
      "Batch ingest PDFs, slides, and scans into Vultr Vision&rsquo;s managed lake while ColPali builds multimodal embeddings.",
    href: "/upload",
    icon: Upload,
  },
  {
    title: "Semantic Search",
    description:
      "Query enterprise corpora through Vultr Vision&rsquo;s retrieval orchestrator tailored for regulated, globally distributed teams.",
    href: "/search",
    icon: Search,
  },
  {
    title: "Vision Chat",
    description:
      "Collaborate on visuals in real time with Vultr Vision copilots and ColPali&rsquo;s reasoning to accelerate reviews and approvals.",
    href: "/chat",
    icon: MessageSquare,
  },
] as const;

const operationsLinks = [
  { title: "Configuration Studio", href: "/configuration", icon: Settings },
  { title: "Maintenance Console", href: "/maintenance", icon: Shield },
] as const;

const stats = [
  {
    value: "32",
    unit: "regions",
    description: "Vultr Vision inference regions keep low-latency retrieval within reach.",
    icon: Globe,
  },
  {
    value: "GPU",
    unit: "fleet",
    description: "Deploy H100, A100, and L40S clusters orchestrated by Vultr Vision without overprovisioning.",
    icon: Cloud,
  },
  {
    value: "99.99%",
    unit: "uptime",
    description: "Reliability your AI workflows demand from the Vultr Vision service plane with transparent SLAs.",
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
    <div className="relative flex flex-1 flex-col bg-white pt-16 dark:bg-vultr-midnight">
      <motion.section
        className="relative isolate overflow-hidden bg-gradient-to-br from-[#06175a] via-[#0d2c96] to-[#1647d1] pb-28 pt-20 text-white sm:pt-24"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(82,186,255,0.25),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(0,123,252,0.35),transparent_60%)]" />
        <div className="relative mx-auto flex max-w-4xl flex-col items-center px-6 text-center sm:px-10">
          <motion.span
            className="eyebrow text-white/70"
            variants={itemVariants}
          >
            Vision Platform Preview
          </motion.span>
          <motion.h1 className="mt-5 max-w-3xl text-digital-h1 text-balance font-bold" variants={itemVariants}>
            Multimodal Document Intelligence with Vultr Vision
          </motion.h1>
          <motion.p className="mt-6 max-w-2xl text-body-lg text-white/85" variants={itemVariants}>
            Vultr Vision orchestrates ingestion, retrieval, and visual reasoning so you can ship document copilots faster.
            Activate upload, semantic search, and vision chat patterns that showcase the Vision design system.
          </motion.p>

          <motion.p className="mt-4 text-body-xs text-white/65" variants={itemVariants}>
            By using this application you agree to the{" "}
            <Link href="https://www.vultr.com/legal/privacy/" target="_blank" rel="noreferrer noopener" className="underline underline-offset-4 hover:text-white">
              GDPR Privacy Notice
            </Link>
            .
          </motion.p>
        </div>

        <div
          aria-hidden="true"
          className="pointer-events-none absolute bottom-0 left-1/2 h-24 w-[160%] -translate-x-1/2 bg-white dark:bg-vultr-midnight"
          style={{ clipPath: "polygon(0 0, 100% 45%, 100% 100%, 0 100%)" }}
        />
      </motion.section>

      <motion.section
        className="bg-white py-24 dark:bg-vultr-midnight"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.25 }}
        variants={containerVariants}
      >
        <div className="layout-container max-w-7xl">
          <motion.div className="flex flex-col items-center text-center" variants={itemVariants}>
            <h2 className="text-editorial-h3 font-semibold text-vultr-navy dark:text-white">
              Build with Vultr Vision blueprints
            </h2>
            <p className="mt-4 max-w-2xl text-body text-vultr-navy/70 dark:text-white/70">
              Every route in this template spotlights a core Vultr Vision capability for ColPali workflows.
              Explore ingestion, operations, and collaboration surfaces anchored in the Vision design language.
            </p>
          </motion.div>

          <motion.div className="mt-16 grid gap-6 md:grid-cols-3" variants={containerVariants}>
            {productCards.map((card) => (
              <motion.div
                key={card.href}
                variants={cardVariants}
                whileHover={{ translateY: -6 }}
                transition={{ type: "spring", stiffness: 200, damping: 22 }}
              >
                <Link
                  href={card.href}
                  className="group flex h-full flex-col justify-between rounded-[var(--radius-card)] border border-black/5 bg-white p-6 text-left shadow-[0_20px_46px_-28px_rgba(9,25,74,0.45)] transition hover:-translate-y-1 hover:border-vultr-blue/35 hover:shadow-[0_24px_52px_-28px_rgba(9,25,74,0.6)] dark:border-white/10 dark:bg-vultr-midnight/80"
                >
                  <div className="space-y-4">
                    <span className="inline-flex size-12 items-center justify-center rounded-[var(--radius-button)] bg-vultr-sky-blue/25 text-vultr-blue dark:bg-vultr-blue-20/30 dark:text-white">
                      <card.icon className="size-icon-sm" />
                    </span>
                    <h3 className="text-digital-h5 font-semibold text-vultr-navy dark:text-white">{card.title}</h3>
                    <p className="text-body-sm text-vultr-navy/70 dark:text-white/75" dangerouslySetInnerHTML={{ __html: card.description }} />
                  </div>
                  <span className="mt-6 inline-flex items-center gap-2 text-body-sm font-medium text-vultr-blue transition group-hover:text-vultr-blue-60 dark:text-vultr-light-blue dark:group-hover:text-white">
                    Explore
                    <ArrowRight className="size-icon-sm transition-transform duration-200 group-hover:translate-x-1.5" />
                  </span>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      <motion.section
        className="bg-gradient-to-b from-white to-[#eef4ff] py-24 dark:from-vultr-midnight dark:to-vultr-blue-20/20"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        variants={containerVariants}
      >
        <div className="layout-container max-w-7xl">
          <motion.div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between" variants={itemVariants}>
            <div className="space-y-3">
              <h2 className="text-editorial-h3 font-semibold text-vultr-navy dark:text-white">
                Operate Vultr Vision everywhere
              </h2>
              <p className="max-w-3xl text-body text-vultr-navy/75 dark:text-white/75">
                Engines, GPUs, and compliance tooling stay aligned wherever workloads land through the Vision control plane.
                Track infrastructure health and keep policies synced with Vultr Vision guardrails.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              {operationsLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="inline-flex items-center gap-2 rounded-[var(--radius-button)] border border-vultr-blue/30 px-4 py-2 text-body-sm font-medium text-vultr-blue transition hover:bg-vultr-blue/10 dark:border-vultr-light-blue/40 dark:text-vultr-light-blue dark:hover:bg-vultr-blue-20/30"
                >
                  <link.icon className="size-icon-2xs" />
                  {link.title}
                </Link>
              ))}
            </div>
          </motion.div>

          <motion.div className="mt-12 grid gap-6 md:grid-cols-3" variants={containerVariants}>
            {stats.map((stat) => (
              <motion.div
                key={stat.description}
                variants={cardVariants}
                className="flex h-full flex-col justify-between rounded-[var(--radius-card)] border border-black/5 bg-white p-6 shadow-[0_20px_46px_-30px_rgba(9,25,74,0.45)] dark:border-white/10 dark:bg-vultr-midnight/80"
              >
                <div className="flex items-start gap-3">
                  <span className="flex size-12 items-center justify-center rounded-[var(--radius-button)] bg-vultr-sky-blue/30 text-vultr-blue dark:bg-vultr-blue-20/30 dark:text-white">
                    <stat.icon className="size-icon-sm" />
                  </span>
                  <div>
                    <p className="text-display-3 font-semibold text-vultr-navy dark:text-white">
                      {stat.value}
                      <span className="ml-1 eyebrow text-vultr-blue-60 dark:text-vultr-light-blue/80">
                        {stat.unit}
                      </span>
                    </p>
                    <p className="mt-2 text-body-sm text-vultr-navy/70 dark:text-white/70">{stat.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      <motion.section
        className="bg-white py-24 dark:bg-vultr-midnight"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        variants={containerVariants}
      >
        <div className="layout-container max-w-6xl">
          <motion.div className="space-y-6 rounded-[var(--radius-card)] border border-black/5 bg-white p-10 shadow-[0_24px_56px_-30px_rgba(9,25,74,0.45)] dark:border-white/10 dark:bg-vultr-midnight/80" variants={itemVariants}>
            <h3 className="text-digital-h5 font-semibold text-vultr-navy dark:text-white">Why teams choose Vultr Vision</h3>
            <ul className="space-y-4 text-body-sm text-vultr-navy/75 dark:text-white/75">
              <li className="flex items-start gap-3">
                <Sparkles className="mt-0.5 size-icon-sm text-vultr-blue" />
                Brings Vultr Vision&rsquo;s design system, states, and interactions directly into your ColPali workflows.
              </li>
              <li className="flex items-start gap-3">
                <Cloud className="mt-0.5 size-icon-sm text-vultr-blue-60" />
                Built atop GPU-ready infrastructure in every Vultr region, orchestrated by the Vision platform to reduce deployment friction.
              </li>
              <li className="flex items-start gap-3">
                <Shield className="mt-0.5 size-icon-sm text-vultr-navy/80 dark:text-white/80" />
                Provides compliance controls, policy management, and observability out of the box via Vision guardrails.
              </li>
            </ul>
            <div className="rounded-[var(--radius-button)] border border-dashed border-vultr-blue/30 bg-vultr-sky-blue/15 px-5 py-4 text-body-sm text-vultr-blue-60 dark:border-vultr-light-blue/40 dark:bg-vultr-blue-20/30 dark:text-vultr-light-blue/90">
              Configure multiple ColPali deployments, enforce policy, and monitor pipelines from a single Vultr Vision console.
            </div>
          </motion.div>
        </div>
      </motion.section>
    </div>
  );
}
