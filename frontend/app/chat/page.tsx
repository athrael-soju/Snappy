"use client";

import { useState } from "react";
import type { ChatMessage } from "@/lib/api/generated";
import { ChatService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import Image from "next/image";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageGroups, setImageGroups] = useState<
    Array<{ url: string | null; label: string | null; score: number | null }[]>
  >([]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    const nextHistory: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(nextHistory);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await ChatService.chatChatPost({
        message: text,
        chat_history: messages,
      });
      // Append assistant response
      const withAssistant: ChatMessage[] = [
        ...nextHistory,
        { role: "assistant", content: res.text },
      ];
      setMessages(withAssistant);
      // Append images to local state for preview
      const group = (res.images || []).map((img: any) => ({
        url: img.image_url ?? null,
        label: img.label ?? null,
        score: typeof img.score === "number" ? img.score : null,
      }));
      setImageGroups((prev) => [...prev, group]);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`${err.status}: ${err.message}`);
      } else {
        setError("Chat failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Chat</h1>

      <div className="space-y-3">
        {messages.length === 0 && (
          <div className="text-sm text-black/60 dark:text-white/60">
            Start the conversation by sending a message.
          </div>
        )}
        {messages.map((m, idx) => (
          <Card key={idx}>
            <CardContent className={`p-3 text-sm ${m.role === "user" ? "bg-black/5 dark:bg-white/10" : ""}`}>
              <div className="font-medium mb-1">
                {m.role === "user" ? "You" : "Assistant"}
              </div>
              <div className="whitespace-pre-wrap">{m.content}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {imageGroups.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-sm font-medium">Retrieved Images</h2>
          {imageGroups.map((group, gIdx) => (
            <div key={gIdx} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {group.map((img, iIdx) => (
                <Card key={iIdx}>
                  <CardContent className="p-2 space-y-2">
                    {img.url && (
                      <Image
                        src={img.url}
                        alt={img.label ?? `Image ${iIdx + 1}`}
                        width={1200}
                        height={800}
                        sizes="(max-width: 640px) 100vw, (max-width: 768px) 50vw, 33vw"
                        className="w-full h-auto rounded"
                      />
                    )}
                    <div className="text-xs">{img.label}</div>
                    {typeof img.score === "number" && (
                      <div className="text-[10px] text-black/60 dark:text-white/60">Score: {img.score.toFixed(3)}</div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ))}
        </div>
      )}

      <form onSubmit={sendMessage} className="flex gap-2 items-start">
        <Input
          placeholder="Ask something about your indexed documents..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <Button type="submit" disabled={loading}>
          {loading ? (
            <span className="inline-flex items-center gap-2"><Spinner size={16} /> Sending...</span>
          ) : (
            "Send"
          )}
        </Button>
      </form>

      {error && <div className="text-red-600 text-sm" role="alert">{error}</div>}
    </div>
  );
}
