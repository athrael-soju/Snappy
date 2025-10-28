"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Clock3,
  Upload,
  Search,
  MessageSquare,
  Settings,
  Shield,
  Sparkles,
  Cloud,
  FileText,
  Globe,
} from "lucide-react";

import { AppButton } from "@/components/app-button";
import {
  MORTY_CENTER_OFFSET,
  MORTY_SIZE,
  MortyHero,
} from "@/components/morty-hero";

const productCards = [
  {
    title: "Visual Upload with Morty",
    description:
      "Let Morty help you upload and process your documents. He&rsquo;ll guide you through visual indexing with ColPali&rsquo;s advanced understanding.",
    href: "/upload",
    icon: Upload,
  },
  {
    title: "Smart Search by Morty",
    description:
      "Morty&rsquo;s visual intelligence finds exactly what you need. Search across images, charts, and text with multimodal precision.",
    href: "/search",
    icon: Search,
  },
  {
    title: "Chat with Morty",
    description:
      "Have a conversation with your Visual Retrieval Buddy. Morty understands your documents and provides grounded, visual answers.",
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

const MIN_MORTY_LEFT = 16;
const DEFAULT_MORTY_LEFT = 32;
const DEFAULT_TRAIL_LEFT = DEFAULT_MORTY_LEFT + MORTY_CENTER_OFFSET;

export default function Home() {
  const heroRef = useRef<HTMLDivElement | null>(null);
  const titleRef = useRef<HTMLHeadingElement | null>(null);
  const [mortyLeft, setMortyLeft] = useState(DEFAULT_MORTY_LEFT);
  const [mortyCenterLeft, setMortyCenterLeft] = useState(DEFAULT_TRAIL_LEFT);

  // Keep Morty aligned with the hero title regardless of text width.
  useEffect(() => {
    const updatePosition = () => {
      if (!heroRef.current || !titleRef.current) {
        return;
      }

      const heroRect = heroRef.current.getBoundingClientRect();
      const titleRect = titleRef.current.getBoundingClientRect();
      const gap = 40;
      const flushLeft = titleRect.left - heroRect.left - MORTY_SIZE;
      const desiredLeft = flushLeft - gap;

      let nextLeft = Math.max(Math.min(desiredLeft, flushLeft), 0);
      if (flushLeft >= MIN_MORTY_LEFT) {
        nextLeft = Math.max(nextLeft, MIN_MORTY_LEFT);
      }

      setMortyLeft((prev) => (Math.abs(prev - nextLeft) < 0.5 ? prev : nextLeft));
      const nextCenter = nextLeft + MORTY_CENTER_OFFSET;
      setMortyCenterLeft((prev) =>
        Math.abs(prev - nextCenter) < 0.5 ? prev : nextCenter,
      );
    };

    const raf = requestAnimationFrame(updatePosition);
    window.addEventListener("resize", updatePosition);

    let observer: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined" && titleRef.current) {
      observer = new ResizeObserver(() => updatePosition());
      observer.observe(titleRef.current);
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", updatePosition);
      observer?.disconnect();
    };
  }, []);

  return (
    <div className="relative flex flex-1 flex-col bg-white pt-16 dark:bg-vultr-midnight">
      <div ref={heroRef} className="relative">
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
              Vultr Vision Platform Preview
            </motion.span>

            <motion.h1
              ref={titleRef}
              className="mt-5 max-w-3xl text-digital-h1 text-balance font-bold"
              variants={itemVariants}
            >
              <span>Meet Morty, Your Visual Retrieval Buddy</span>{" "}
              <span className="text-body-xs font-semibold text-white/85">Powered by </span>
              <Link
                href="https://github.com/athrael-soju/Snappy"
                target="_blank"
                rel="noreferrer noopener"
                className="text-body-xs font-semibold text-white/85 underline underline-offset-8 hover:text-white"
              >
                Snappy
              </Link>
            </motion.h1>
            <motion.p className="mt-6 max-w-2xl text-body-lg text-white/85" variants={itemVariants}>
              Morty combines the global Vultr infrastructure with advanced ColPali vision models to help you find, understand, and chat with your documents like never before. Your friendly mascot makes multimodal document intelligence effortless.
            </motion.p>

            {/* Welcome message from Morty - appears on mobile/tablet */}
            <motion.div
              className="mt-4 flex items-center gap-3 rounded-full bg-white/10 px-4 py-2 backdrop-blur-sm lg:hidden"
              variants={itemVariants}
            >
              <div>
                <Image
                  src="/vultr/morty/super_morty_nobg.png"
                  alt="Morty"
                  width={128}
                  height={128}
                  className="rounded-full"
                />
              </div>
              <span className="text-body-xs text-white/90">
                Hey there! I&rsquo;m Morty, your Visual Retrieval Buddy 🚀
              </span>
            </motion.div>

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

        <div className="pointer-events-none absolute inset-0">
          <MortyHero
            mortyLeft={mortyLeft}
            mortyCenterLeft={mortyCenterLeft}
          />
        </div>
      </div>

      {/* Meet Morty Section */}
      <motion.section
        className="bg-gradient-to-b from-white to-vultr-sky-blue/10 py-24 dark:from-vultr-midnight dark:to-vultr-blue-20/20"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.25 }}
        variants={containerVariants}
      >
        <div className="layout-container max-w-6xl">
          <motion.div
            className="grid gap-12 items-center lg:grid-cols-2"
            variants={containerVariants}
          >
            <motion.div className="space-y-6" variants={itemVariants}>
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full bg-vultr-blue/10 px-4 py-2 text-body-sm font-semibold text-vultr-blue">
                  <Sparkles className="size-icon-xs" />
                  Meet Your Visual Retrieval Buddy
                </div>
                <h2 className="text-editorial-h2 font-bold text-vultr-navy dark:text-white">
                  Morty Makes Document Intelligence Personal
                </h2>
                <p className="text-body-lg text-vultr-navy/70 dark:text-white/70">
                  More than just a mascot, Morty is your intelligent companion who understands the visual context of your documents. He combines Vultr&rsquo;s powerful infrastructure with ColPali&rsquo;s advanced vision models to deliver insights that go beyond simple text search.
                </p>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="flex size-8 items-center justify-center rounded-full bg-vultr-blue/10 text-vultr-blue">
                    <Sparkles className="size-icon-xs" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-vultr-navy dark:text-white">Visual Understanding</h3>
                    <p className="text-body-sm text-vultr-navy/70 dark:text-white/70">Morty sees charts, diagrams, and layouts just like you do</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex size-8 items-center justify-center rounded-full bg-vultr-blue/10 text-vultr-blue">
                    <MessageSquare className="size-icon-xs" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-vultr-navy dark:text-white">Conversational Intelligence</h3>
                    <p className="text-body-sm text-vultr-navy/70 dark:text-white/70">Chat naturally about your documents with grounded, visual responses</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="flex size-8 items-center justify-center rounded-full bg-vultr-blue/10 text-vultr-blue">
                    <Globe className="size-icon-xs" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-vultr-navy dark:text-white">Global Performance</h3>
                    <p className="text-body-sm text-vultr-navy/70 dark:text-white/70">Powered by Vultr&rsquo;s worldwide infrastructure for instant results</p>
                  </div>
                </div>
              </div>
            </motion.div>
            <motion.div className="relative" variants={itemVariants}>
              <div className="relative">
                {/* Background glow effect */}
                <motion.div
                  className="absolute inset-0 scale-110 rounded-full bg-gradient-to-r from-vultr-blue/20 via-purple-500/20 to-pink-500/20 blur-3xl"
                  animate={{
                    opacity: [0.35, 0.75, 0.35],
                    scale: [1.1, 1.22, 1.1],
                  }}
                  transition={{
                    duration: 5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
                <div className="relative flex items-center justify-center">
                  <motion.div
                    className="relative flex w-full max-w-sm flex-col gap-4 rounded-3xl border border-white/20 bg-white/70 p-6 text-left shadow-xl backdrop-blur-md dark:border-white/15 dark:bg-vultr-midnight/60"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.4, ease: "easeOut" }}
                  >
                    <div className="space-y-1">
                      <p className="text-body-xs font-semibold uppercase tracking-wide text-vultr-navy/60 dark:text-white/60">
                        Morty status snapshot
                      </p>
                      <h3 className="text-body font-semibold text-vultr-navy dark:text-white">
                        Visual intelligence ready
                      </h3>
                    </div>
                    <div className="grid gap-3">
                      <div className="flex items-start gap-3 rounded-2xl border border-vultr-blue/20 bg-vultr-sky-blue/10 p-3 dark:border-vultr-light-blue/25 dark:bg-vultr-midnight/40">
                        <Sparkles className="mt-0.5 size-icon-sm text-vultr-blue" />
                        <div>
                          <p className="text-body-sm font-semibold text-vultr-navy dark:text-white">Model cache primed</p>
                          <p className="text-body-xs text-vultr-navy/70 dark:text-white/70">
                            ColPali embeddings warmed to serve multimodal prompts without cold starts.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3 rounded-2xl border border-vultr-blue/15 bg-white/70 p-3 dark:border-vultr-light-blue/20 dark:bg-vultr-midnight/40">
                        <FileText className="mt-0.5 size-icon-sm text-vultr-blue" />
                        <div>
                          <p className="text-body-sm font-semibold text-vultr-navy dark:text-white">48k vectors online</p>
                          <p className="text-body-xs text-vultr-navy/70 dark:text-white/70">
                            Qdrant collections stay synced with the latest batches ready for retrieval.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3 rounded-2xl border border-vultr-blue/10 bg-white/60 p-3 dark:border-vultr-light-blue/15 dark:bg-vultr-midnight/35">
                        <Clock3 className="mt-0.5 size-icon-sm text-vultr-blue" />
                        <div>
                          <p className="text-body-sm font-semibold text-vultr-navy dark:text-white">1.4s median response</p>
                          <p className="text-body-xs text-vultr-navy/70 dark:text-white/70">
                            Morty streams answers with citations ready to inspect the matching PDF page.
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
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
              Morty&rsquo;s Visual Intelligence Suite
            </h2>
            <p className="mt-4 max-w-2xl text-body text-vultr-navy/70 dark:text-white/70">
              Let Morty guide you through powerful document intelligence features. From visual uploads to smart chat,
              your friendly retrieval buddy makes every interaction intuitive and effective.
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
            <h3 className="text-digital-h5 font-semibold text-vultr-navy dark:text-white">Why teams love working with Morty</h3>
            <ul className="space-y-4 text-body-sm text-vultr-navy/75 dark:text-white/75">
              <li className="flex items-start gap-3">
                <Sparkles className="mt-0.5 size-icon-sm text-vultr-blue" />
                Morty makes complex visual retrieval accessible with intuitive interactions and friendly guidance.
              </li>
              <li className="flex items-start gap-3">
                <Cloud className="mt-0.5 size-icon-sm text-vultr-blue-60" />
                Your Visual Retrieval Buddy leverages Vultr&rsquo;s global GPU infrastructure for lightning-fast document processing.
              </li>
              <li className="flex items-start gap-3">
                <Shield className="mt-0.5 size-icon-sm text-vultr-navy/80 dark:text-white/80" />
                Morty ensures your documents are processed securely with enterprise-grade compliance and privacy controls.
              </li>
            </ul>
            <div className="rounded-[var(--radius-button)] border border-dashed border-vultr-blue/30 bg-vultr-sky-blue/15 px-5 py-4 text-body-sm text-vultr-blue-60 dark:border-vultr-light-blue/40 dark:bg-vultr-blue-20/30 dark:text-vultr-light-blue/90">
              💫 &ldquo;Morty transforms how we interact with documents - it&rsquo;s like having a visual intelligence expert on our team!&rdquo; - Happy User
            </div>
          </motion.div>
        </div>
      </motion.section>
    </div>
  );
}
