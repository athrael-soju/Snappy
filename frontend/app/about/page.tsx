"use client";

import { AboutContent } from "@/components/about";
import { Info } from "lucide-react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";
import { GlassPanel } from "@/components/ui/glass-panel";

export default function AboutPage() {
  return (
    <motion.div {...defaultPageMotion} className="mx-auto w-full max-w-[1160px] h-full px-4 sm:px-6 lg:px-8">
      {/* Page stack */}
      <div className="flex h-full flex-col gap-6 py-6">
        {/* Header card */}
        <motion.div variants={sectionVariants} className="flex-shrink-0">
          <GlassPanel className="rounded-2xl bg-white/70 p-4 shadow">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
                <Info className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <h1 className="text-xl font-semibold">About the ColPali Template</h1>
                <p className="text-sm text-muted-foreground">A friendly and lightweight knowledge base platform with visual document understanding</p>
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* Content section - scrollable */}
        <motion.div variants={sectionVariants} className="flex-1 min-h-0">
          <div 
            className="h-full overflow-y-auto rounded-2xl bg-white/70 p-8 shadow"
            style={{ overscrollBehavior: 'contain', scrollbarGutter: 'stable' }}
          >
            <div className="max-w-4xl mx-auto">
              <AboutContent />
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
