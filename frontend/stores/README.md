# Morty™ App Store Architecture

Morty’s client-side state management system mirrors the structure introduced in Snappy, now updated with Morty branding and documentation.

## Structure

```
stores/
├── app-store.tsx          # Provider and context
├── types.ts               # Shared types for state and actions
├── reducers/              # Domain-specific reducers
│   ├── index.ts           # Reducer composition
│   ├── search-reducer.ts  # Search state
│   ├── chat-reducer.ts    # Chat state
│   ├── upload-reducer.ts  # Upload workflow
│   ├── system-reducer.ts  # System status
│   └── global-reducer.ts  # Hydration and page tracking
├── hooks/                 # Domain hooks
│   ├── index.ts
│   ├── use-search-store.ts
│   ├── use-chat-store.ts
│   ├── use-upload-store.ts
│   ├── use-system-status.ts
│   └── use-upload-sse.ts  # Upload SSE management
└── utils/
    └── storage.ts        # LocalStorage helpers
```

## Usage

### Provider

```tsx
import { AppStoreProvider } from '@/stores/app-store';

export function MortyApp() {
  return (
    <AppStoreProvider>
      <YourApp />
    </AppStoreProvider>
  );
}
```

### Domain Hooks

```tsx
import { useSearchStore } from '@/stores/app-store';

export function SearchPane() {
  const { query, results, setQuery, setResults } = useSearchStore();
  // Component logic here
}
```

Available hooks:

- `useSearchStore()` – Search state and actions  
- `useChatStore()` – Chat state and actions  
- `useUploadStore()` – Upload state and actions  
- `useSystemStatus()` – System health and maintenance status  
- `useUploadSse()` – Server-Sent Event lifecycle for the upload page

### Direct Access

```tsx
import { useAppStore } from '@/stores/app-store';

export function AdvancedComponent() {
  const { state, dispatch } = useAppStore();
  // Direct access to the full store
}
```

## Benefits

1. Separation of concerns: reducers, hooks, and utilities stay focused.  
2. Maintainability: each domain evolves independently.  
3. Testability: reducers and utilities are easy to unit test.  
4. Scalability: add domains without touching existing code.  
5. Type safety: shared types guard actions and selectors.  
6. Reusability: hooks centralize repeated logic for UI components.

## Adding Features

### New Action

1. Define the action type in `types.ts`.  
2. Update the relevant reducer under `reducers/`.  
3. Expose the action through the matching hook.

### New Domain

1. Add domain types to `types.ts`.  
2. Create `reducers/<domain>-reducer.ts`.  
3. Register it in `reducers/index.ts`.  
4. Add `hooks/use-<domain>-store.ts`.  
5. Export the hook from `app-store.tsx`.

---

Morty is a rebrand based on the open-source project Snappy (https://github.com/athrael-soju/Snappy). Portions are licensed under the **MIT License**; license and attribution preserved.
