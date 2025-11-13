/**
 * Type definitions for OpenAI Responses API messages and events
 * Based on OpenAI SDK types for the Responses API
 */

export type MessageRole = "system" | "user" | "assistant";

export type MessageContentItem =
  | { type: "input_text"; text: string }
  | { type: "input_image"; image_url: string }
  | { type: "text"; text: string }
  | { type: "function_call"; call_id: string; name: string; arguments: string }
  | { type: "function_call_output"; call_id: string; output: string };

export interface Message {
  role: MessageRole;
  content: MessageContentItem[];
}

export interface FunctionCallOutput {
  type: "function_call";
  call_id: string;
  name: string;
  arguments: string;
}

export interface FunctionCallOutputMessage {
  type: "function_call_output";
  call_id: string;
  output: string;
}

export interface SearchToolResult {
  success: boolean;
  query: string;
  images?: string[];
  results?: unknown[];
  count?: number;
  error?: string;
}

// Stream event types from OpenAI Responses API
export type StreamEventType =
  | "response.created"
  | "response.done"
  | "response.output.item.added"
  | "response.output.item.done"
  | "response.text.delta"
  | "response.text.done"
  | "response.function_call.delta"
  | "response.function_call.done"
  | "error";

export interface StreamEvent {
  type: StreamEventType;
  [key: string]: unknown;
}

export interface TextDeltaEvent extends StreamEvent {
  type: "response.text.delta";
  delta: string;
}

export interface TextDoneEvent extends StreamEvent {
  type: "response.text.done";
  text: string;
}

export interface ErrorEvent extends StreamEvent {
  type: "error";
  error: {
    message: string;
    type: string;
    code?: string;
  };
}

// Custom SSE event wrapper
export interface SSEEvent {
  event: string;
  data: unknown;
}

export interface KBImagesEvent {
  event: "kb.images";
  data: {
    items: unknown[];
  };
}
