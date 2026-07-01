---
title: Component API
sort: 110
section-id: api-reference
keywords: defineComponent, ref, computed, watch, component API, reactive
description: Complete reference for the Velox component API — defineComponent, ref, computed, and watch
language: en
---

# Component API

This page documents the core component primitives exported from `velox/client`.

## `signal(initialValue)`

Creates a reactive signal — a value container that triggers DOM updates when changed.

```typescript
import { signal } from 'velox/client';

const count = signal(0);
count.value;        // read: 0
count.value = 5;    // write: triggers reactive updates
count.peek();       // read without tracking (no reactive subscription)
```

### Type Signature

```typescript
function signal<T>(initialValue: T): Signal<T>;

interface Signal<T> {
  value: T;
  peek(): T;
  subscribe(listener: (value: T) => void): () => void;
}
```

## `computed(fn)`

Creates a derived reactive value. Re-evaluates lazily when accessed and a dependency has changed.

```typescript
import { signal, computed } from 'velox/client';

const price = signal(100);
const taxRate = signal(0.2);
const total = computed(() => price.value * (1 + taxRate.value));

total.value; // 120
price.value = 200;
total.value; // 240
```

Computed signals are read-only — attempting to set `.value` throws.

## `effect(fn)`

Registers a reactive side effect. Runs immediately, then again whenever its signal dependencies change.

```typescript
import { signal, effect } from 'velox/client';

const query = signal('');

const dispose = effect(() => {
  console.log('query =', query.value);
  // runs now, then on every change to query.value
});

// Clean up manually (effects inside components clean up on unmount):
dispose();
```

Return a cleanup function from the effect to run before the next execution or on disposal:

```typescript
effect(() => {
  const controller = new AbortController();
  fetchData(query.value, controller.signal);
  return () => controller.abort();
});
```

## `batch(fn)`

Groups multiple signal writes into a single reactive update pass:

```typescript
import { batch } from 'velox/client';

batch(() => {
  a.value = 1;
  b.value = 2;
  c.value = 3;
  // Only one round of re-renders happens
});
```

## `untrack(fn)`

Execute a function without tracking its signal reads as dependencies:

```typescript
import { signal, effect, untrack } from 'velox/client';

const a = signal(1);
const b = signal(2);

effect(() => {
  // Only subscribes to `a`, not `b`
  const result = a.value + untrack(() => b.value);
  console.log(result);
});
```

## Lifecycle Hooks

Lifecycle hooks must be called synchronously during component initialisation (similar to React rules of hooks, but without the runtime check overhead).

### `onMount(fn)`

Called after the component's DOM is inserted into the document:

```typescript
import { onMount } from 'velox/client';

onMount(() => {
  // safe to access DOM, start timers, etc.
  const input = document.querySelector('#my-input') as HTMLInputElement;
  input.focus();
});
```

### `onCleanup(fn)`

Called before the component unmounts, or before an effect runs again. Use to cancel subscriptions, abort requests, and clear timers:

```typescript
import { onMount, onCleanup } from 'velox/client';

onMount(() => {
  const timer = setInterval(tick, 1000);
  onCleanup(() => clearInterval(timer));
});
```

### `onDestroy(fn)`

Like `onCleanup`, but only runs when the component is permanently destroyed (not before re-renders):

```typescript
import { onDestroy } from 'velox/client';

onDestroy(() => {
  analytics.trackLeave(route);
});
```

## `createContext` / `useContext`

Create a context for dependency injection without prop drilling:

```typescript
import { createContext, useContext } from 'velox/client';

// Create context with a default value
const ThemeContext = createContext<'light' | 'dark'>('light');

// Provide a value to a subtree
<ThemeContext.Provider value="dark">
  <App />
</ThemeContext.Provider>

// Consume in any descendant
function Button() {
  const theme = useContext(ThemeContext);
  return <button class={`btn--${theme}`}>Click</button>;
}
```

## `ref()`

Create a DOM element reference:

```typescript
import { ref, onMount } from 'velox/client';

export default function TextInput() {
  const inputRef = ref<HTMLInputElement>();

  onMount(() => {
    inputRef.current?.focus();
  });

  return <input ref={inputRef} type="text" />;
}
```

## `defineComponent(options)`

The explicit component definition API — useful when you need named components for debugging or when defining components programmatically:

```typescript
import { defineComponent, signal } from 'velox/client';

const Counter = defineComponent({
  name: 'Counter',
  props: {
    initialValue: { type: Number, default: 0 },
    step: { type: Number, default: 1 },
  },
  setup(props) {
    const count = signal(props.initialValue);
    const increment = () => { count.value += props.step; };
    const decrement = () => { count.value -= props.step; };

    return { count, increment, decrement };
  },
  render({ count, increment, decrement }) {
    return (
      <div class="counter">
        <button onClick={decrement}>−</button>
        <span>{count}</span>
        <button onClick={increment}>+</button>
      </div>
    );
  },
});

export default Counter;
```

## `lazy(loader)`

Lazily load a component — its code is only downloaded when the component is first rendered:

```typescript
import { lazy } from 'velox/client';

const HeavyChart = lazy(() => import('./HeavyChart.tsx'));

// Use in JSX — shows nothing while loading by default
<HeavyChart data={data} />

// With a Suspense boundary for a loading state
import { Suspense } from 'velox';

<Suspense fallback={<Skeleton />}>
  <HeavyChart data={data} />
</Suspense>
```

## `memo(component)`

Wrap a component in `memo` to skip re-renders when props have not changed (shallow equality):

```typescript
import { memo } from 'velox/client';

const ExpensiveList = memo(function ExpensiveList({ items }: { items: string[] }) {
  return <ul>{items.map(i => <li>{i}</li>)}</ul>;
});
```

Accepts a custom equality function as the second argument:

```typescript
const MyComponent = memo(Component, (prev, next) => prev.id === next.id);
```
