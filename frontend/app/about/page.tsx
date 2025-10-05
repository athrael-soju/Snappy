"use client";

import AboutContent from "@/components/about-content";
import { PageHeader } from "@/components/page-header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Info } from "lucide-react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";

export default function AboutPage() {
  return (
    <motion.div {...defaultPageMotion} className="page-shell page-section flex flex-col min-h-0 flex-1">
      <motion.section variants={sectionVariants}>
        <PageHeader
          title="About This Template"
          description="A friendly and lightweight knowledge base platform with visual document understanding."
          icon={Info}
        />
      </motion.section>
      <motion.section variants={sectionVariants} className="flex-1 min-h-0">
        <ScrollArea className="flex-1 min-h-0">
          <div className="pb-10">
            <AboutContent />
          </div>
        </ScrollArea>
      </motion.section>
    </motion.div>
  );
}
