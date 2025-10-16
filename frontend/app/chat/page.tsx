"use client";

import { ChangeEvent } from "react";
import "@/lib/api/client";
import { useChat } from "@/lib/hooks/use-chat";
import { useSystemStatus } from "@/stores/app-store";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function ChatPage() {
  const {
    input,
    setInput,
    messages,
    loading,
    error,
    timeToFirstTokenMs,
    k,
    setK,
    toolCallingEnabled,
    setToolCallingEnabled,
    maxTokens,
    setMaxTokens,
    isSettingsValid,
    sendMessage,
    reset,
  } = useChat();
  const { isReady } = useSystemStatus();

  const handleNumberChange = (event: ChangeEvent<HTMLInputElement>, setter: (value: number) => void) => {
    const next = Number.parseInt(event.target.value, 10);
    if (!Number.isNaN(next)) {
      setter(next);
    }
  };

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Ask follow-up questions and explore indexed documents. This minimal chat keeps only the core features needed to talk to the backend.
        </p>
        {!isReady && (
          <p className="text-sm text-red-600 dark:text-red-400">
            The system is not ready. Initialize storage before sending prompts.
          </p>
        )}
      </header>

      <section className="space-y-3 rounded border border-border p-4 text-sm">
        <h2 className="text-base font-semibold text-foreground">Retrieval Settings</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex flex-col gap-1">
            <span>Neighbors (k)</span>
            <input
              type="number"
              min={1}
              value={k}
              onChange={(event) => handleNumberChange(event, setK)}
              className="rounded border border-border px-3 py-2"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span>Max tokens</span>
            <input
              type="number"
              min={64}
              value={maxTokens}
              onChange={(event) => handleNumberChange(event, setMaxTokens)}
              className="rounded border border-border px-3 py-2"
            />
          </label>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={toolCallingEnabled}
              onChange={(event) => setToolCallingEnabled(event.target.checked)}
            />
            <span>Allow tool calling</span>
          </label>
        </div>
        {!isSettingsValid && (
          <p className="text-xs text-red-600 dark:text-red-400">The selected k value is not valid.</p>
        )}
        {timeToFirstTokenMs !== null && (
          <p className="text-xs text-muted-foreground">
            Last response latency: {(timeToFirstTokenMs / 1000).toFixed(2)}s to first token.
          </p>
        )}
      </section>

      <section className="flex-1 space-y-3 rounded border border-border p-4">
        <h2 className="text-base font-semibold text-foreground">Conversation</h2>
        <ScrollArea className="h-[480px] rounded border border-dashed border-border">
          <div className="space-y-4 p-3">
          {messages.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No messages yet. Type a question below and press enter to get started.
            </p>
          ) : (
            messages.map((message) => (
              <article
                key={message.id}
                className="space-y-2 rounded bg-muted p-3 text-sm"
              >
                <header className="font-semibold text-foreground">
                  {message.role === "user" ? "You" : "Assistant"}
                </header>
                <p className="whitespace-pre-wrap text-foreground">{message.content || (message.role === "assistant" ? "..." : "")}</p>
                {message.citations && message.citations.length > 0 && (
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {message.citations.map((item, index) => (
                      <li key={index}>
                        {item.url ? (
                          <a href={item.url} target="_blank" rel="noreferrer" className="text-primary underline">
                            {item.label ?? item.url}
                          </a>
                        ) : (
                          <span>{item.label ?? "Referenced item"}</span>
                        )}
                        {typeof item.score === "number" && (
                          <span className="ml-1">({Math.round(item.score * 100)}%)</span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </article>
            ))
          )}
          {loading && (
            <p className="text-xs text-muted-foreground">Assistant is responding...</p>
          )}
          </div>
        </ScrollArea>
      </section>

      <form onSubmit={sendMessage} className="space-y-2 rounded border border-border p-4">
        <label className="flex flex-col gap-1 text-sm">
          Your question
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            rows={3}
            className="resize-y rounded border border-border px-3 py-2"
            placeholder="Ask anything about your documents."
            disabled={!isReady}
          />
        </label>

        <div className="flex flex-wrap gap-3 text-sm">
          <button
            type="submit"
            className="rounded bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
            disabled={loading || !isReady || !input.trim() || !isSettingsValid}
          >
            {loading ? "Sending..." : "Send"}
          </button>
          <button
            type="button"
            onClick={reset}
            className="rounded border border-border px-4 py-2 text-foreground disabled:opacity-50"
            disabled={messages.length === 0 && !input}
          >
            Clear conversation
          </button>
        </div>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      </form>
    </main>
  );
}
