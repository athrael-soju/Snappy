# App Store Architecture

This directory contains the refactored application state management system, organized by separation of concerns.

## Structure

```
stores/
├── app-store.tsx          # Main store provider and context
├── types.ts               # Type definitions for state and actions
├── reducers/              # Domain-specific reducers
│   ├── index.ts           # Main reducer composition
│   ├── search-reducer.ts  # Search state logic
│   ├── chat-reducer.ts    # Chat state logic
│   ├── upload-reducer.ts  # Upload state logic
│   ├── system-reducer.ts  # System status logic
│   └── global-reducer.ts  # Global actions (hydration, page tracking)
├── hooks/                 # Domain-specific hooks
│   ├── index.ts           # Hook exports
│   ├── use-search-store.ts
│   ├── use-chat-store.ts
│   ├── use-upload-store.ts
│   ├── use-system-status.ts
│   └── use-upload-sse.ts  # SSE connection management for uploads
└── utils/                 # Utility functions
    └── storage.ts         # LocalStorage serialization/deserialization
```

## Usage

### Using the Store Provider

Wrap your app with the provider:

```tsx
import { AppStoreProvider } from '@/stores/app-store';

<AppStoreProvider>
  <YourApp />
</AppStoreProvider>
```

### Using Domain Hooks

Import and use the specific hook you need:

```tsx
import { useSearchStore } from '@/stores/app-store';

function SearchComponent() {
  const { query, results, setQuery, setResults } = useSearchStore();
  // ... component logic
}
```

Available hooks:
- `useSearchStore()` - Search state and actions
- `useChatStore()` - Chat state and actions
- `useUploadStore()` - Upload state and actions
- `useSystemStatus()` - System status and health checks

### Accessing Raw State/Dispatch

For advanced use cases:

```tsx
import { useAppStore } from '@/stores/app-store';

function Component() {
  const { state, dispatch } = useAppStore();
  // Direct access to full state and dispatch
}
```

## Benefits of This Architecture

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Maintainability** - Easy to locate and modify specific functionality
3. **Testability** - Individual reducers and utilities can be tested in isolation
4. **Scalability** - New domains can be added without modifying existing code
5. **Type Safety** - Centralized types ensure consistency across the application
6. **Code Reusability** - Utilities and hooks can be shared across components

## Adding New Features

### Adding a New Action

1. Add the action type to `types.ts`
2. Create/update the appropriate reducer in `reducers/`
3. Add action creators to the relevant hook in `hooks/`

### Adding a New Domain

1. Define types in `types.ts`
2. Create a new reducer in `reducers/[domain]-reducer.ts`
3. Add reducer to composition in `reducers/index.ts`
4. Create a new hook in `hooks/use-[domain]-store.ts`
5. Export the hook from `app-store.tsx`
