"use client";

import React from "react";
import { motion } from "framer-motion";
import { fadeInItemMotion, hoverLift, staggeredListMotion } from "@/lib/motion-presets";
import { Badge } from "@/components/ui/badge";
import { HelpCircle } from "lucide-react";

export interface StarterQuestionItem {
  icon: React.ComponentType<{ className?: string }>;
  text: string;
  category: string;
}

export interface StarterQuestionsProps {
  questions: StarterQuestionItem[];
  onSelect: (text: string) => void;
}

export default function StarterQuestions({ questions, onSelect }: StarterQuestionsProps) {
  return (
    <div className="w-full max-w-3xl space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <HelpCircle className="w-4 h-4 text-purple-500" />
        <span className="text-xs font-medium text-muted-foreground">Try asking:</span>
      </div>
      <motion.div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5" {...staggeredListMotion}>
        {questions.map((question, idx) => {
          const Icon = question.icon;
          return (
            <motion.button
              key={idx}
              {...fadeInItemMotion}
              {...hoverLift}
              type="button"
              onClick={() => onSelect(question.text)}
              className="flex w-full items-start gap-3 rounded-xl border border-dashed border-muted bg-[color:var(--surface-1)]/70 p-3 text-left transition-all duration-200 group hover:border-primary/40 hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
            >
              <div className="flex items-start gap-2.5">
                <div className="flex-shrink-0 rounded-lg border border-muted bg-[color:var(--surface-2)]/80 p-1.5 text-primary transition group-hover:border-primary/40 group-hover:text-primary">
                  <Icon className="w-3.5 h-3.5 text-purple-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground transition-colors group-hover:text-primary line-clamp-2">
                    {question.text}
                  </p>
                  <Badge variant="outline" className="mt-2 border border-muted bg-[color:var(--surface-0)]/70 px-2 py-0.5 text-[10px] font-medium text-muted-foreground group-hover:border-primary/40 group-hover:text-primary">
                    {question.category}
                  </Badge>
                </div>
              </div>
            </motion.button>
          );
        })}
      </motion.div>
    </div>
  );
}

