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
              className="p-3 text-left rounded-lg border-2 border-dashed border-purple-200/50 hover:border-purple-400 hover:bg-gradient-to-br hover:from-blue-50/50 hover:to-purple-50/50 transition-all duration-300 group shadow-sm hover:shadow-md"
            >
              <div className="flex items-start gap-2.5">
                <div className="p-1.5 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg group-hover:from-blue-200 group-hover:to-purple-200 transition-all duration-300 shadow-sm flex-shrink-0">
                  <Icon className="w-3.5 h-3.5 text-purple-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground group-hover:text-purple-700 transition-colors leading-snug line-clamp-2">
                    {question.text}
                  </p>
                  <Badge variant="outline" className="text-[10px] mt-1.5 border-purple-200/50 group-hover:border-purple-300 group-hover:bg-purple-50/50 px-1.5 py-0">
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
