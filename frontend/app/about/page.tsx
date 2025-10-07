"use client";

import AboutContent from "@/components/about-content";
import { PageHeader } from "@/components/page-header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Info } from "lucide-react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";

export default function AboutPage() {
  return (
    <motion.div {...defaultPageMotion} className="page-shell flex flex-col min-h-0 flex-1 gap-6">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
        <PageHeader
          title="About the ColPali Template"
          icon={Info}
          tooltip="A friendly and lightweight knowledge base platform with visual document understanding"
        />
      </motion.section>
      <motion.section variants={sectionVariants} className="flex-1 min-h-0 pb-6 sm:pb-8 flex">
        <Card className="card-surface mx-auto w-full max-w-4xl flex min-h-0 flex-1 flex-col overflow-hidden border-border/50 shadow-lg">
          <ScrollArea className="h-[calc(100vh-20rem)] rounded-xl">
            <div className="p-8">
              <AboutContent />
            </div>
          </ScrollArea>
        </Card>
      </motion.section>
    </motion.div>
  );
}
