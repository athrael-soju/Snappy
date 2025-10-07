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
    <div className="w-full max-w-3xl space-y-2.5">
      <div className="flex items-center gap-2">
        <div className="flex h-4 w-4 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
          <HelpCircle className="w-2.5 h-2.5 text-white" />
        </div>
        <span className="text-xs font-semibold text-foreground">Try asking</span>
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
              className="flex w-full items-start gap-2.5 rounded-lg border border-muted/60 bg-[color:var(--surface-1)]/50 p-2.5 text-left transition-all duration-200 group hover:border-purple-500/40 hover:bg-gradient-to-br hover:from-purple-500/5 hover:to-blue-500/5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500/30"
            >
              <div className="flex items-start gap-2.5 w-full">
                <div className="flex-shrink-0 rounded-lg bg-gradient-to-br from-purple-500/10 to-blue-500/10 p-1.5 transition-transform group-hover:scale-110">
                  <Icon className="w-3.5 h-3.5 text-purple-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground transition-colors group-hover:text-purple-600 line-clamp-2 leading-snug">
                    {question.text}
                  </p>
                  <Badge variant="outline" className="mt-1.5 border-muted/60 bg-[color:var(--surface-0)]/50 px-1.5 py-0 text-[9px] font-semibold text-muted-foreground/80 group-hover:border-purple-500/40 group-hover:text-purple-600">
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

