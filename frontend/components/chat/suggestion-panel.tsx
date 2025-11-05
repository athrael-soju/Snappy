"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Telescope, ClipboardCheck, MessageCircle, Wand2 } from "lucide-react";

export type StarterPrompt = {
    title: string;
    description: string;
    tag: string;
    icon: typeof Telescope;
    emoji?: string;
    prompt: string;
};

export const STARTER_PROMPTS: StarterPrompt[] = [
    {
        title: "Find visual information",
        description: "Search for charts, diagrams, or images showing specific data or concepts.",
        tag: "Visual",
        icon: Telescope,
        prompt: "Find all charts and diagrams related to [your topic] and describe what they show.",
    },
    {
        title: "Extract from tables",
        description: "Pull specific data from tables and structured content in documents.",
        tag: "Data",
        icon: ClipboardCheck,
        prompt: "What information is shown in the tables about [your topic]? List the key data points.",
    },
    {
        title: "Analyze document layout",
        description: "Understand how information is organized across pages and sections.",
        tag: "Layout",
        icon: MessageCircle,
        prompt: "Describe the layout and structure of documents covering [your topic]. Where is the key information located?",
    },
    {
        title: "Compare visual elements",
        description: "Identify differences and similarities between images and diagrams.",
        tag: "Compare",
        icon: Wand2,
        prompt: "Compare the visual elements across different documents about [your topic]. What patterns or differences do you notice?",
    },
];

type StarterPromptCardProps = {
    prompt: StarterPrompt;
    onSelect: (value: string) => void;
    index: number;
};

function StarterPromptCard({ prompt, onSelect, index }: StarterPromptCardProps) {
    return (
        <motion.button
            key={prompt.prompt}
            type="button"
            onClick={() => onSelect(prompt.prompt)}
            className="group relative overflow-hidden rounded-xl border border-border/20 bg-background/90 p-3 sm:p-4 text-left shadow-xs transition hover:border-primary/50 hover:shadow-md hover:shadow-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 touch-manipulation"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.1, duration: 0.3 }}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-chart-1/5 opacity-0 transition group-hover:opacity-100" />
            <div className="relative flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2">
                    <div className="flex size-icon-lg flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary shadow-sm">
                        <prompt.icon className="size-icon-sm" />
                    </div>
                    <Badge
                        variant="outline"
                        className="flex-shrink-0 rounded-full border-primary/30 px-2 py-0.5 text-body-xs uppercase tracking-wide text-primary"
                    >
                        {prompt.tag}
                    </Badge>
                </div>
                <h3 className="text-body-xs sm:text-body-sm font-semibold text-foreground leading-tight">
                    {prompt.title}
                </h3>
                <p className="text-body-xs text-muted-foreground line-clamp-2 leading-snug">{prompt.description}</p>
            </div>
        </motion.button>
    );
}

type SuggestionPanelProps = {
    onSelect: (value: string) => void;
    recentQuestions: Array<{ id: string; content: string }>;
};

export function SuggestionPanel({ onSelect, recentQuestions }: SuggestionPanelProps) {
    return (
        <div className="w-full max-w-3xl space-y-3 rounded-xl border border-border/20 bg-card/60 p-4 shadow-sm animate-in fade-in duration-500 dark:bg-card/40">
            <div className="space-y-2.5">
                <div className="flex items-center justify-center gap-2 text-body-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    <Sparkles className="size-icon-sm text-primary" />
                    Try asking
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                    {STARTER_PROMPTS.map((prompt, index) => (
                        <StarterPromptCard key={prompt.prompt} prompt={prompt} index={index} onSelect={onSelect} />
                    ))}
                </div>
            </div>
            <RecentQuestionsList questions={recentQuestions} onSelect={onSelect} />
        </div>
    );
}

type RecentQuestionsListProps = {
    questions: Array<{ id: string; content: string }>;
    onSelect: (content: string) => void;
};

function RecentQuestionsList({ questions, onSelect }: RecentQuestionsListProps) {
    if (questions.length === 0) {
        return null;
    }

    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2 text-body-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <MessageCircle className="size-icon-sm" />
                Recent questions
            </div>
            <div className="flex flex-wrap gap-2">
                {questions.map((item, index) => (
                    <motion.button
                        key={item.id}
                        type="button"
                        onClick={() => onSelect(item.content)}
                        className="group inline-flex items-center gap-2 rounded-full border border-border/25 bg-background/85 px-4 py-2 text-body-xs text-muted-foreground transition hover:border-primary/50 hover:text-foreground touch-manipulation"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1, duration: 0.2 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <MessageCircle className="size-icon-sm text-primary transition group-hover:text-primary" />
                        <span className="line-clamp-1">{item.content}</span>
                    </motion.button>
                ))}
            </div>
        </div>
    );
}
