"use client";

import type { ChangeEvent, FormEvent } from "react";
import { motion } from "framer-motion";
import { Loader2, Send, Settings, Trash2, AlertCircle } from "lucide-react";
import { AppButton } from "@/components/app-button";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";

export type ChatComposerProps = {
    input: string;
    onInputChange: (value: string) => void;
    isReady: boolean;
    loading: boolean;
    isSendDisabled: boolean;
    toolCallingEnabled: boolean;
    onToolToggle: (checked: boolean) => void;
    k: number;
    maxTokens: number;
    onKChange: (value: number) => void;
    onMaxTokensChange: (value: number) => void;
    reasoningEffort: "minimal" | "low" | "medium" | "high";
    onReasoningChange: (value: "minimal" | "low" | "medium" | "high") => void;
    summaryPreference: "auto" | "concise" | "detailed" | null;
    onSummaryChange: (value: "auto" | "concise" | "detailed" | null) => void;
    isSettingsValid: boolean;
    sendMessage: (event: FormEvent<HTMLFormElement>) => void;
    error: string | null;
    onReset: () => void;
    hasMessages: boolean;
};

export function ChatComposer({
    input,
    onInputChange,
    isReady,
    loading,
    isSendDisabled,
    toolCallingEnabled,
    onToolToggle,
    k,
    maxTokens,
    onKChange,
    onMaxTokensChange,
    reasoningEffort,
    onReasoningChange,
    summaryPreference,
    onSummaryChange,
    isSettingsValid,
    sendMessage,
    error,
    onReset,
    hasMessages,
}: ChatComposerProps) {
    const handleNumberChange = (
        event: ChangeEvent<HTMLInputElement>,
        setter: (value: number) => void,
    ) => {
        const nextValue = Number.parseInt(event.target.value, 10);
        if (!Number.isNaN(nextValue)) {
            setter(nextValue);
        }
    };

    return (
        <motion.form
            onSubmit={sendMessage}
            className="sticky bottom-0 left-0 right-0 z-10 px-4 pb-10 sm:px-6"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
        >
            <div className="mx-auto w-full max-w-6xl space-y-3">
                <div className="relative overflow-hidden rounded-[32px] border border-border/40 bg-background/95 p-4 shadow-xl shadow-primary/5 backdrop-blur">
                    <div className="pointer-events-none absolute inset-0 rounded-[32px] border border-white/5" />
                    <div className="relative z-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
                        <div className="flex-1">
                            <div className="rounded-3xl border border-border/30 bg-input/10 transition focus-within:border-primary/40 focus-within:shadow-lg focus-within:shadow-primary/10">
                                <Textarea
                                    id="chat-input-area"
                                    value={input}
                                    onChange={(event) => onInputChange(event.target.value)}
                                    placeholder="Ask anything about your documents..."
                                    disabled={!isReady}
                                    rows={3}
                                    className="min-h-[3.5rem] w-full resize-none border-0 bg-transparent px-4 py-3 text-body leading-relaxed placeholder:text-muted-foreground outline-none focus-visible:ring-0"
                                />
                            </div>
                        </div>
                        <div className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row sm:items-center sm:gap-3">
                            <AppButton
                                type="submit"
                                size="icon-lg"
                                variant="hero"
                                elevated
                                disabled={isSendDisabled}
                                aria-label="Send message"
                            >
                                {loading ? <Loader2 className="size-icon-md animate-spin" /> : <Send className="size-icon-md" />}
                            </AppButton>
                            <div className="inline-flex items-center overflow-hidden rounded-full border border-border/40 bg-background/80 shadow-sm divide-x divide-border/40">
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <AppButton
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            groupPosition="start"
                                            aria-label="Open retrieval settings"
                                        >
                                            <Settings className="size-icon-sm" />
                                        </AppButton>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-80 space-y-4">
                                        <div>
                                            <h4 className="text-body-sm font-semibold text-foreground">Retrieval settings</h4>
                                            <p className="mt-1 text-body-xs text-muted-foreground">
                                                Tune how many neighbors to fetch and how long responses can be.
                                            </p>
                                        </div>
                                        <div className="space-y-4 text-body-sm">
                                            <div className="space-y-2">
                                                <Label htmlFor="chat-k">Top K</Label>
                                                <Input
                                                    id="chat-k"
                                                    type="number"
                                                    min={1}
                                                    value={k}
                                                    onChange={(event) => handleNumberChange(event, onKChange)}
                                                />
                                                <p className="text-body-xs text-muted-foreground">
                                                    Controls how many nearest neighbors the assistant retrieves. Higher values surface more
                                                    context but may introduce noise.
                                                </p>
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="chat-max-tokens">Max tokens</Label>
                                                <Input
                                                    id="chat-max-tokens"
                                                    type="number"
                                                    min={64}
                                                    value={maxTokens}
                                                    onChange={(event) => handleNumberChange(event, onMaxTokensChange)}
                                                />
                                                <p className="text-body-xs text-muted-foreground">
                                                    Control response length to balance speed with detail.
                                                </p>
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="chat-reasoning">Reasoning effort</Label>
                                                <Select
                                                    value={reasoningEffort}
                                                    onValueChange={(value) =>
                                                        onReasoningChange(value as "minimal" | "low" | "medium" | "high")
                                                    }
                                                >
                                                    <SelectTrigger id="chat-reasoning" className="w-full justify-between">
                                                        <SelectValue placeholder="Choose effort" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="minimal">Minimal</SelectItem>
                                                        <SelectItem value="low">Low</SelectItem>
                                                        <SelectItem value="medium">Medium</SelectItem>
                                                        <SelectItem value="high">High</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <p className="text-body-xs text-muted-foreground">
                                                    Increase effort to give the model more reasoning compute before answering.
                                                </p>
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="chat-summary">Response summary</Label>
                                                <Select
                                                    value={summaryPreference ?? "none"}
                                                    onValueChange={(value) =>
                                                        onSummaryChange(value === "none" ? null : (value as "auto" | "concise" | "detailed"))
                                                    }
                                                >
                                                    <SelectTrigger id="chat-summary" className="w-full justify-between">
                                                        <SelectValue placeholder="No summary" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="none">None</SelectItem>
                                                        <SelectItem value="auto">Auto</SelectItem>
                                                        <SelectItem value="concise">Concise</SelectItem>
                                                        <SelectItem value="detailed">Detailed</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <p className="text-body-xs text-muted-foreground">
                                                    Request an additional summary alongside the full answer when supported.
                                                </p>
                                            </div>
                                            <div className="flex items-center justify-between gap-3 rounded-xl border border-border/30 bg-card/40 px-3 py-2">
                                                <div>
                                                    <p className="text-body-sm font-medium text-foreground">Allow tool calling</p>
                                                    <p className="text-body-xs text-muted-foreground">
                                                        Let the assistant call retrieval tools when needed.
                                                    </p>
                                                </div>
                                                <Switch
                                                    id="chat-tool-calling"
                                                    checked={toolCallingEnabled}
                                                    onCheckedChange={onToolToggle}
                                                />
                                            </div>
                                            {!isSettingsValid && (
                                                <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-body-xs text-destructive">
                                                    <AlertCircle className="size-icon-sm" />
                                                    The selected Top K value is not valid.
                                                </div>
                                            )}
                                        </div>
                                    </PopoverContent>
                                </Popover>
                                <AppButton
                                    type="button"
                                    onClick={onReset}
                                    variant="ghost"
                                    size="icon"
                                    groupPosition="end"
                                    disabled={!hasMessages && !input}
                                    aria-label="Clear conversation"
                                >
                                    <Trash2 className="size-icon-sm" />
                                </AppButton>
                            </div>
                        </div>
                    </div>
                </div>
                {error && (
                    <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-body-sm font-medium text-destructive">
                        <AlertCircle className="size-icon-sm" />
                        {error}
                    </div>
                )}
            </div>
        </motion.form>
    );
}
