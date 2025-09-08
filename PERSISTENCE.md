# Data Persistence Implementation

This implementation adds data persistence across page navigation for the FastAPI/Next.js/ColPali template.

## Features Added

### 🔄 Global State Management
- **App Store**: Centralized state management using React Context and useReducer
- **LocalStorage Integration**: Automatic persistence of app state to browser storage
- **Type-Safe Actions**: Strongly typed actions and state updates

### 📄 Search Page Persistence
- **Query & Results**: Search queries and results are preserved
- **Search Settings**: K value and other search parameters persist
- **Recent Searches**: Search history maintained across sessions

### 💬 Chat Page Persistence  
- **Conversation History**: Complete message history preserved
- **Visual Citations**: Image groups and citations persist with messages
- **Chat Settings**: K value and tool calling preferences saved

### 📤 Upload Page Persistence
- **Progress Tracking**: Upload progress and status preserved (for ongoing uploads)
- **Error/Success States**: Messages and job status maintained
- **File State**: File selection state (excluding actual FileList objects)

### 🎯 Visual Indicators
- **Navigation Badges**: Show data counts in navigation bar
- **Restoration Banners**: Inform users when data has been restored
- **Smart Timing**: Banners only show when returning to pages with data

## Implementation Details

### Core Components

1. **`stores/app-store.tsx`** - Global state management
   - Centralized app state with search, chat, and upload sections
   - Automatic localStorage persistence with debouncing
   - Type-safe actions and reducers

2. **`components/data-restored-banner.tsx`** - User feedback
   - Shows when data has been restored on page return
   - Allows users to clear persisted data
   - Auto-dismisses after 5 seconds

3. **`hooks/use-page-visit-banner.ts`** - Smart banner logic
   - Tracks page visits to determine when to show restoration banners
   - Prevents showing banners on initial page loads
   - Manages banner visibility state

### Modified Pages

- **Search Page**: Uses `useSearchStore()` for persistence
- **Chat Page**: Updated `useChat()` hook to work with global store  
- **Upload Page**: Uses `useUploadStore()` for progress persistence
- **Navigation**: Shows data indicators with counts

### Data Serialization

- **Safe Persistence**: Non-serializable objects (like FileList) are excluded
- **Debounced Saves**: LocalStorage writes are debounced to prevent excessive operations
- **Error Handling**: Graceful fallbacks if localStorage is unavailable

## Testing

Visit `/test-persistence` to:
1. Add sample data to each section
2. Navigate between pages
3. Verify data persistence and restoration banners
4. Test clearing functionality

## Usage Examples

### Adding Custom Persistent State

```typescript
// 1. Add to AppState interface
interface AppState {
  // ... existing state
  myFeature: {
    data: string[];
    settings: Record<string, any>;
  };
}

// 2. Add action types
type AppAction = 
  // ... existing actions
  | { type: 'MY_FEATURE_SET_DATA'; payload: string[] };

// 3. Add reducer case
case 'MY_FEATURE_SET_DATA':
  return { 
    ...state, 
    myFeature: { 
      ...state.myFeature, 
      data: action.payload 
    } 
  };

// 4. Create convenience hook
export function useMyFeatureStore() {
  const { state, dispatch } = useAppStore();
  return {
    ...state.myFeature,
    setData: (data: string[]) => 
      dispatch({ type: 'MY_FEATURE_SET_DATA', payload: data }),
  };
}
```

### Using in Components

```typescript
function MyComponent() {
  const { data, setData } = useMyFeatureStore();
  
  // Component will automatically persist and restore data
  return (
    <div>
      {data.map(item => <div key={item}>{item}</div>)}
      <button onClick={() => setData([...data, 'new item'])}>
        Add Item
      </button>
    </div>
  );
}
```

## Benefits

1. **Improved UX**: Users don't lose work when navigating
2. **Session Continuity**: Data survives page refreshes and navigation
3. **Progressive Enhancement**: Works without backend changes
4. **Type Safety**: Full TypeScript support prevents errors
5. **Performance**: Debounced persistence prevents excessive storage writes
6. **User Control**: Clear data options give users control

## Browser Support

- **Modern Browsers**: Full support with localStorage
- **Legacy Fallback**: Graceful degradation if localStorage unavailable
- **Memory Management**: Automatic cleanup of old data

This implementation provides a robust foundation for maintaining user data across navigation while being extensible for future features.
