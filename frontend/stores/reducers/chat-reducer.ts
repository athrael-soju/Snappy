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
    
    case 'CHAT_SET_TOP_K':
      return { ...state, chat: { ...state.chat, topK: action.payload } };
    
    case 'CHAT_SET_MAX_TOKENS':
      return { ...state, chat: { ...state.chat, maxTokens: action.payload } };
    
    case 'CHAT_RESET':
      // Preserve user settings when clearing conversation
      return { 
        ...state, 
        chat: { 
          ...initialState.chat,
          k: state.chat.k,
          toolCallingEnabled: state.chat.toolCallingEnabled,
          topK: state.chat.topK,
          maxTokens: state.chat.maxTokens,
        } 
      };
    
    default:
      return null;
  }
}
