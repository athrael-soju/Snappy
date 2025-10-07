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
    <div className="w-full space-y-3">
      <motion.div className="grid grid-cols-1 sm:grid-cols-2 gap-3" {...staggeredListMotion}>
        {questions.map((question, idx) => {
          const Icon = question.icon;
          return (
            <motion.button
              key={idx}
              {...fadeInItemMotion}
              {...hoverLift}
              type="button"
              onClick={() => onSelect(question.text)}
              className="flex w-full items-start gap-3 rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-3.5 text-left transition-all duration-200 group hover:border-primary/50 hover:bg-card/80 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
            >
              <div className="flex items-start gap-3 w-full">
                <div className="flex-shrink-0 rounded-lg bg-gradient-to-br from-primary/10 to-primary/5 p-2 transition-transform group-hover:scale-105">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground transition-colors group-hover:text-primary line-clamp-2 leading-relaxed">
                    {question.text}
                  </p>
                  <Badge variant="outline" className="mt-2 border-border/50 bg-background/50 px-2 py-0.5 text-xs font-medium text-muted-foreground group-hover:border-primary/50 group-hover:text-primary">
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

