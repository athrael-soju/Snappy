/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatMessage } from './ChatMessage';
export type ChatRequest = {
    message: string;
    chat_history?: (Array<ChatMessage> | null);
    'k'?: (number | null);
    ai_enabled?: (boolean | null);
    temperature?: (number | null);
    system_prompt?: (string | null);
};

