import { useAppStore } from '@/stores/app-store';
import type { ChatMessage } from "@/lib/hooks/use-chat";

/**
 * Hook for accessing and managing chat state
 */
export function useChatStore() {
  const { state, dispatch } = useAppStore();
  
  return {
    ...state.chat,
    setMessages: (messages: ChatMessage[]) => 
      dispatch({ type: 'CHAT_SET_MESSAGES', payload: messages }),
    addMessage: (message: ChatMessage) => 
      dispatch({ type: 'CHAT_ADD_MESSAGE', payload: message }),
    updateLastMessage: (content: string) => 
      dispatch({ type: 'CHAT_UPDATE_LAST_MESSAGE', payload: content }),
    updateMessageCitations: (messageId: string, citations: Array<{ url: string | null; label: string | null; score: number | null }>) => 
      dispatch({ type: 'CHAT_UPDATE_MESSAGE_CITATIONS', payload: { messageId, citations } }),
    setImageGroups: (imageGroups: Array<{ url: string | null; label: string | null; score: number | null }>[]) => 
      dispatch({ type: 'CHAT_SET_IMAGE_GROUPS', payload: imageGroups }),
    setK: (k: number) => dispatch({ type: 'CHAT_SET_K', payload: k }),
    setToolCallingEnabled: (enabled: boolean) => 
      dispatch({ type: 'CHAT_SET_TOOL_CALLING', payload: enabled }),
    setLoading: (loading: boolean) => 
      dispatch({ type: 'CHAT_SET_LOADING', payload: loading }),
    setMaxTokens: (maxTokens: number) => dispatch({ type: 'CHAT_SET_MAX_TOKENS', payload: maxTokens }),
    setReasoningEffort: (effort: 'minimal' | 'low' | 'medium' | 'high') =>
      dispatch({ type: 'CHAT_SET_REASONING_EFFORT', payload: effort }),
    setSummaryPreference: (summary: 'auto' | 'concise' | 'detailed' | null) =>
      dispatch({ type: 'CHAT_SET_SUMMARY_PREFERENCE', payload: summary }),
    removeEmptyAssistantPlaceholder: () => 
      dispatch({ type: 'CHAT_REMOVE_EMPTY_ASSISTANT' }),
    reset: () => dispatch({ type: 'CHAT_RESET' }),
  };
}
