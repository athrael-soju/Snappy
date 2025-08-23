"use client";

import React from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Lightbulb } from "lucide-react";

export interface ExampleQuery {
  text: string;
  category: string;
}

export interface ExampleQueriesProps {
  examples: ExampleQuery[];
  onSelect: (text: string) => void;
  loading?: boolean;
}

const categoryEmoji = (category: string) => {
  switch (category) {
    case "Documents":
      return "📄";
    case "Presentations":
      return "🖥️";
    case "Analysis":
      return "📊";
    case "Photos":
      return "📷";
    case "Technical":
      return "🛠️";
    case "Legal":
      return "📜";
    default:
      return "✨";
  }
};

export default function ExampleQueries({ examples, onSelect, loading }: ExampleQueriesProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Lightbulb className="w-4 h-4 text-yellow-500" />
        <span className="text-sm font-medium text-muted-foreground">Try these examples:</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {examples.map((example, idx) => (
          <motion.button
            key={idx}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSelect(example.text)}
            disabled={!!loading}
            className="text-left p-3 rounded-lg border border-muted-foreground/20 hover:border-blue-300 hover:bg-blue-50/30 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="text-sm font-medium text-foreground group-hover:text-blue-700 transition-colors">
              {categoryEmoji(example.category)} "{example.text}"
            </div>
            <Badge variant="outline" className="text-xs mt-1">
              {example.category}
            </Badge>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
