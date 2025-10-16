"use client"

import { ChangeEvent, FormEvent } from "react"
import "@/lib/api/client"

import { Page, PageSection } from "@/components/layout/page"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { useChat } from "@/lib/hooks/use-chat"
import { useSystemStatus } from "@/stores/app-store"

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
  } = useChat()
  const { isReady } = useSystemStatus()

  const handleNumberChange = (
    event: ChangeEvent<HTMLInputElement>,
    setter: (value: number) => void,
  ) => {
    const next = Number.parseInt(event.target.value, 10)
    if (!Number.isNaN(next)) {
      setter(next)
    }
  }

  const disableReset = messages.length === 0 && !input

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!loading && isReady && input.trim() && isSettingsValid) {
      await sendMessage(event)
    }
  }

  return (
    <Page
      title="Chat"
      description="Ask follow-up questions and explore indexed documents with a minimal conversational interface."
      actions={
        <Button
          variant="outline"
          size="sm"
          onClick={reset}
          disabled={disableReset}
        >
          New chat
        </Button>
      }
    >
      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Retrieval settings</CardTitle>
            <CardDescription>
              Tune retrieval parameters before starting a conversation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            {!isSettingsValid && (
              <Alert variant="destructive">
                <AlertTitle>Invalid configuration</AlertTitle>
                <AlertDescription>
                  The current neighbors value is not valid. Adjust the input
                  below.
                </AlertDescription>
              </Alert>
            )}

            <div className="grid gap-(--space-section-stack) sm:grid-cols-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="chat-neighbors">Neighbors (k)</Label>
                <Input
                  id="chat-neighbors"
                  type="number"
                  min={1}
                  value={k}
                  onChange={(event) => handleNumberChange(event, setK)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="chat-max-tokens">Max tokens</Label>
                <Input
                  id="chat-max-tokens"
                  type="number"
                  min={64}
                  value={maxTokens}
                  onChange={(event) => handleNumberChange(event, setMaxTokens)}
                />
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  id="allow-tool-calls"
                  checked={toolCallingEnabled}
                  onCheckedChange={(checked) =>
                    setToolCallingEnabled(Boolean(checked))
                  }
                />
                <Label htmlFor="allow-tool-calls">Allow tool calling</Label>
              </div>
            </div>

            {timeToFirstTokenMs !== null && (
              <Badge variant="outline" className="w-fit">
                First token {(timeToFirstTokenMs / 1000).toFixed(2)}s
              </Badge>
            )}
          </CardContent>
        </Card>
      </PageSection>

      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Conversation</CardTitle>
            <CardDescription>
              Messages appear here after you submit a prompt.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            {!isReady && (
              <Alert variant="destructive">
                <AlertTitle>System not ready</AlertTitle>
                <AlertDescription>
                  Initialize storage before sending prompts.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex max-h-96 flex-col gap-4 overflow-y-auto rounded-lg border border-border/60 bg-card/30 p-4">
              {messages.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No messages yet. Type a question below to get started.
                </p>
              ) : (
                messages.map((message) => (
                  <article
                    key={message.id}
                    className="space-y-2 rounded-lg border border-border/60 bg-card/60 p-3 text-sm"
                  >
                    <header className="font-semibold text-foreground">
                      {message.role === "user" ? "You" : "Assistant"}
                    </header>
                    <p className="whitespace-pre-wrap text-foreground">
                      {message.content ||
                        (message.role === "assistant" ? "..." : "")}
                    </p>
                    {message.citations && message.citations.length > 0 && (
                      <ul className="space-y-1 text-xs text-muted-foreground">
                        {message.citations.map((item, index) => (
                          <li key={index}>
                            {item.url ? (
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-primary underline"
                              >
                                {item.label ?? item.url}
                              </a>
                            ) : (
                              <span>{item.label ?? "Referenced item"}</span>
                            )}
                            {typeof item.score === "number" && (
                              <span className="ml-1">
                                ({Math.round(item.score * 100)}%)
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                ))
              )}
              {loading && (
                <p className="text-xs text-muted-foreground">
                  Assistant is responding...
                </p>
              )}
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertTitle>Chat failed</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
          <CardFooter>
            <form
              onSubmit={handleSubmit}
              className="flex w-full flex-col gap-3"
            >
              <div className="flex flex-col gap-2 text-sm">
                <Label htmlFor="chat-input">Your question</Label>
                <Textarea
                  id="chat-input"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  rows={3}
                  placeholder="Ask anything about your documents."
                  disabled={!isReady}
                />
              </div>

              <div className="flex flex-wrap gap-3 text-sm">
                <Button
                  type="submit"
                  disabled={
                    loading || !isReady || !input.trim() || !isSettingsValid
                  }
                >
                  {loading ? "Sending..." : "Send"}
                </Button>
              </div>
            </form>
          </CardFooter>
        </Card>
      </PageSection>
    </Page>
  )
}
