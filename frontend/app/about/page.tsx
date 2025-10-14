"use client";

import { motion } from "framer-motion";
import { Info } from "lucide-react";

import AboutContent from "@/components/about-content";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const fadeIn = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3, ease: "easeOut" },
};

export default function AboutPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <motion.div {...fadeIn}>
        <PageHeader
          title="About Snappy"
          description="Snappy is a starter kit for multimodal retrieval. Learn the stack, configuration options, and how to extend the template."
          icon={Info}
          badge={
            <Badge variant="secondary" className="rounded-full px-3 py-1 text-xs font-medium">
              Mobile ready layout
            </Badge>
          }
        />
      </motion.div>

      <motion.section {...fadeIn} transition={{ ...fadeIn.transition, delay: 0.1 }}>
        <Card className="rounded-3xl border bg-card p-6 shadow-sm sm:p-10">
          <AboutContent />
        </Card>
      </motion.section>
    </div>
  );
}
