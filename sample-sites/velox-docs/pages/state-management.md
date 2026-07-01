---
title: State Management
sort: 120
section-id: core-concepts
keywords: state, signals, store, reactive, computed, effect, state management
description: Velox's reactive state management system — signals, stores, and reactive primitives
language: en
---

# State Management

Velox uses a signals-based reactivity system for client-side state. Signals are fine-grained reactive primitives — when a signal's value changes, only the DOM nodes that actually read that signal update. There is no virtual DOM diffing, no component tree re-render, and no unnecessary reconciliation.

## Signals

A signal is a reactive value container:

```typescript
import { signal } from 'velox/client';

const count = signal(0);

// Read the current value
console.log(count.value); // 0

// Update the value
count.value = 1;
console.log(count.value); // 1
```

In JSX, signals are automatically unwrapped — you do not need `.value` in templates:

```tsx
const count = signal(0);

// Both are equivalent:
<p>{count.value}</p>
<p>{count}</p>
```

The second form (`{count}` without `.value`) subscribes the DOM node directly to the signal. This is more efficient because Velox skips the component function entirely and updates only the text node when the signal changes.

## Computed Signals

A computed signal derives its value from one or more other signals. It re-evaluates automatically when its dependencies change:

```typescript
import { signal, computed } from 'velox/client';

const firstName = signal('Jane');
const lastName = signal('Doe');
const fullName = computed(() => `${firstName.value} ${lastName.value}`);

console.log(fullName.value); // "Jane Doe"
firstName.value = 'John';
console.log(fullName.value); // "John Doe"
```

Computed signals are lazy and memoised — the computation only runs when the value is read, and only re-runs if a dependency has changed since the last read.

## Effects

An effect runs a side effect whenever its reactive dependencies change:

```typescript
import { signal, effect } from 'velox/client';

const query = signal('');

effect(() => {
  console.log('Search query changed:', query.value);
  // this re-runs every time query.value changes
});
```

Effects clean themselves up automatically when the component unmounts. To clean up manually within an effect (e.g., cancel a previous request):

```typescript
effect(() => {
  const controller = new AbortController();
  fetch(`/api/search?q=${query.value}`, { signal: controller.signal })
    .then(r => r.json())
    .then(results => resultsSignal.value = results);

  return () => controller.abort(); // cleanup function
});
```

## Stores

For shared state across components, define a store. A store is a module that encapsulates signals and exposes a clean interface:

```typescript
// lib/stores/cart.ts
import { signal, computed } from 'velox/client';

export interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

const items = signal<CartItem[]>([]);

export const cartStore = {
  items,
  total: computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  ),
  itemCount: computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0)
  ),

  addItem(item: Omit<CartItem, 'quantity'>) {
    const existing = items.value.find(i => i.id === item.id);
    if (existing) {
      items.value = items.value.map(i =>
        i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
      );
    } else {
      items.value = [...items.value, { ...item, quantity: 1 }];
    }
  },

  removeItem(id: string) {
    items.value = items.value.filter(i => i.id !== id);
  },

  clear() {
    items.value = [];
  },
};
```

Use the store in any component — signals are module-level singletons:

```tsx
import { cartStore } from '$lib/stores/cart';

export default function CartIcon() {
  return (
    <button>
      Cart ({cartStore.itemCount})
    </button>
  );
}
```

## Batch Updates

Multiple signal updates within a `batch()` call are processed as a single reactive update, preventing intermediate renders:

```typescript
import { signal, batch } from 'velox/client';

const x = signal(0);
const y = signal(0);
const z = signal(0);

// Without batch: triggers 3 re-renders
x.value = 1;
y.value = 2;
z.value = 3;

// With batch: triggers 1 re-render
batch(() => {
  x.value = 1;
  y.value = 2;
  z.value = 3;
});
```

## Async Signals

For async data that needs to integrate with the reactivity system, use `asyncSignal`:

```typescript
import { signal, asyncSignal } from 'velox/client';

const userId = signal<string | null>(null);

const userProfile = asyncSignal(async () => {
  if (!userId.value) return null;
  const res = await fetch(`/api/users/${userId.value}`);
  return res.json();
});

// userProfile.value is: { status: 'idle' | 'loading' | 'success' | 'error', data, error }
```

In JSX:

```tsx
<div>
  {userProfile.value.status === 'loading' && <Spinner />}
  {userProfile.value.status === 'success' && (
    <p>Hello, {userProfile.value.data.name}</p>
  )}
  {userProfile.value.status === 'error' && (
    <p>Error: {userProfile.value.error.message}</p>
  )}
</div>
```

## Server State with `@velox/query`

For server state (data fetched from APIs), the `@velox/query` package provides a higher-level solution with caching, revalidation, and optimistic updates:

```typescript
import { createQuery, createMutation } from '@velox/query';

const postsQuery = createQuery({
  key: ['posts'],
  fetcher: () => fetch('/api/posts').then(r => r.json()),
  staleTime: 60_000, // data is fresh for 60 seconds
});

const createPostMutation = createMutation({
  mutator: (data) => fetch('/api/posts', { method: 'POST', body: JSON.stringify(data) }),
  onSuccess: () => postsQuery.invalidate(),
});
```

## Persisting State

To persist signal state to `localStorage` or `sessionStorage`:

```typescript
import { persistedSignal } from 'velox/client';

const theme = persistedSignal('theme', 'light', {
  storage: 'localStorage',
});
```

The signal is initialised from storage on mount and written back whenever it changes.

## Reactive Context (Dependency Injection)

For providing state to deeply nested component trees without prop drilling, use the context API:

```typescript
import { createContext, useContext } from 'velox/client';

const ThemeContext = createContext<'light' | 'dark'>('light');

// Provider (wraps a subtree)
<ThemeContext.Provider value={currentTheme}>
  <App />
</ThemeContext.Provider>

// Consumer (anywhere in the tree below)
function ThemedButton() {
  const theme = useContext(ThemeContext);
  return <button class={`btn btn--${theme}`}>Click me</button>;
}
```
