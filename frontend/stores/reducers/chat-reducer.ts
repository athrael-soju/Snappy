import type { AppState, AppAction } from '../types';
import { initialState } from '../types';

export function chatReducer(state: AppState, action: AppAction): AppState | null {
  switch (action.type) {
    case 'CHAT_SET_MESSAGES':
      return { ...state, chat: { ...state.chat, messages: action.payload } };
    
    case 'CHAT_ADD_MESSAGE':
      return { ...state, chat: { ...state.chat, messages: [...state.chat.messages, action.payload] } };
    
    case 'CHAT_UPDATE_LAST_MESSAGE':
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: state.chat.messages.map((msg, idx) =>
            idx === state.chat.messages.length - 1 ? { ...msg, content: action.payload } : msg
          ),
        },
      };
    
    case 'CHAT_UPDATE_MESSAGE_CITATIONS':
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: state.chat.messages.map((msg) =>
            msg.id === action.payload.messageId ? { ...msg, citations: action.payload.citations } : msg
          ),
        },
      };
    
    case 'CHAT_SET_IMAGE_GROUPS':
      return { ...state, chat: { ...state.chat, imageGroups: action.payload } };
    
    case 'CHAT_SET_K':
      return { ...state, chat: { ...state.chat, k: action.payload } };
    
    case 'CHAT_SET_TOOL_CALLING':
      return { ...state, chat: { ...state.chat, toolCallingEnabled: action.payload } };
    
    case 'CHAT_SET_LOADING':
      return { ...state, chat: { ...state.chat, loading: action.payload } };
    
    case 'CHAT_SET_MAX_TOKENS':
      return { ...state, chat: { ...state.chat, maxTokens: action.payload } };

    case 'CHAT_SET_REASONING_EFFORT':
      return { ...state, chat: { ...state.chat, reasoningEffort: action.payload } };

    case 'CHAT_SET_SUMMARY_PREFERENCE':
      return { ...state, chat: { ...state.chat, summaryPreference: action.payload } };

    case 'CHAT_REMOVE_EMPTY_ASSISTANT': {
      const messages = state.chat.messages;
      if (messages.length === 0) {
        return state;
      }
      const last = messages[messages.length - 1];
      if (last.role !== 'assistant' || (last.content ?? '').trim().length > 0) {
        return state;
      }
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: messages.slice(0, -1),
        },
      };
    }
    
    case 'CHAT_RESET':
      // Preserve user settings when clearing conversation
      return { 
        ...state, 
        chat: { 
          ...initialState.chat,
          k: state.chat.k,
          toolCallingEnabled: state.chat.toolCallingEnabled,
          maxTokens: state.chat.maxTokens,
          reasoningEffort: state.chat.reasoningEffort,
          summaryPreference: state.chat.summaryPreference,
        } 
      };
    
    default:
      return null;
  }
}
