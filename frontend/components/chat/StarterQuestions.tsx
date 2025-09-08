"use client";

import React from "react";
import { motion } from "framer-motion";
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
    <div className="w-full max-w-2xl space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <HelpCircle className="w-5 h-5 text-primary" />
        <span className="text-sm font-medium text-muted-foreground">Try asking:</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {questions.map((question, idx) => {
          const Icon = question.icon;
          return (
            <motion.button
              key={idx}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(question.text)}
              className="p-4 text-left rounded-xl border-2 border-dashed border-border hover:border-primary hover:bg-primary/5 transition-all group"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-secondary rounded-lg group-hover:bg-accent transition-colors">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                    {question.text}
                  </p>
                  <Badge variant="outline" className="text-xs mt-2 group-hover:border-primary">
                    {question.category}
                  </Badge>
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
