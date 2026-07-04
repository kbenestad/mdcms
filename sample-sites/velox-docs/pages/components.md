---
title: Components
sort: 110
section-id: core-concepts
keywords: components, props, slots, lifecycle, tsx, velox components, islands
description: The Velox component model, including props, slots, lifecycle hooks, and the islands architecture
language: en
---

# Components

Velox components are TypeScript/TSX files that describe a piece of UI. They are the fundamental building blocks of a Velox application — reusable, composable, and by default rendered entirely on the server.

## Defining a Component

A basic Velox component is a TypeScript function that returns JSX:

```tsx
// components/Greeting.tsx
interface GreetingProps {
  name: string;
  formal?: boolean;
}

export default function Greeting({ name, formal = false }: GreetingProps) {
  const salutation = formal ? 'Good day' : 'Hello';
  return <p>{salutation}, {name}!</p>;
}
```

Use it in a route or another component:

```tsx
---
import Greeting from '../components/Greeting.tsx';
---

<main>
  <Greeting name="Alice" />
  <Greeting name="Bob" formal />
</main>
```

## Props

Props are typed using TypeScript interfaces or types. All props are validated at compile time — no runtime prop checking overhead.

```tsx
interface CardProps {
  title: string;
  description: string;
  href?: string;
  variant?: 'default' | 'featured' | 'compact';
  children?: VeloxNode;
}

export default function Card({
  title,
  description,
  href,
  variant = 'default',
  children,
}: CardProps) {
  return (
    <div class={`card card--${variant}`}>
      <h3>{href ? <a href={href}>{title}</a> : title}</h3>
      <p>{description}</p>
      {children && <div class="card__body">{children}</div>}
    </div>
  );
}
```

### Default Props

Set default values directly in the destructuring parameter, as shown above. Velox does not use a separate `defaultProps` mechanism.

### Required vs Optional Props

By TypeScript convention, optional props are marked with `?`. Omitting a required prop is a compile-time error.

## Slots

The `children` prop is the default slot — content placed between the opening and closing tags of a component:

```tsx
<Card title="Welcome" description="Get started">
  <p>This is the card body.</p>
</Card>
```

### Named Slots

For more complex component APIs, use named slot props:

```tsx
interface ModalProps {
  title: VeloxNode;
  footer?: VeloxNode;
  children: VeloxNode;
}

export default function Modal({ title, footer, children }: ModalProps) {
  return (
    <div class="modal">
      <div class="modal__header">{title}</div>
      <div class="modal__body">{children}</div>
      {footer && <div class="modal__footer">{footer}</div>}
    </div>
  );
}
```

Usage:

```tsx
<Modal
  title={<h2>Confirm Delete</h2>}
  footer={
    <>
      <button onClick={cancel}>Cancel</button>
      <button onClick={confirm}>Delete</button>
    </>
  }
>
  <p>Are you sure you want to delete this item?</p>
</Modal>
```

## Server vs Client Components

By default, all Velox components run on the server. They have no JavaScript bundle size on the client and cannot use browser APIs or client-side reactivity.

To make a component interactive on the client, use the `client:*` hydration directive when you include it in a route:

```tsx
---
import Counter from '../components/Counter.tsx';
import LazyChart from '../components/LazyChart.tsx';
---

<!-- Hydrate immediately when page loads -->
<Counter client:load />

<!-- Hydrate when browser is idle -->
<Counter client:idle />

<!-- Hydrate when the component enters the viewport -->
<LazyChart client:visible />

<!-- Hydrate only when a media query matches -->
<Sidebar client:media="(max-width: 768px)" />
```

### Writing Client Components

Client components can use signals, effects, and browser APIs:

```tsx
import { signal, effect, onMount, onCleanup } from 'velox/client';

export default function LiveClock() {
  const time = signal(new Date().toLocaleTimeString());

  onMount(() => {
    const interval = setInterval(() => {
      time.value = new Date().toLocaleTimeString();
    }, 1000);

    onCleanup(() => clearInterval(interval));
  });

  return <p>Current time: {time}</p>;
}
```

## Lifecycle Hooks

Client-side components can use the following lifecycle hooks:

| Hook | When it runs |
|------|-------------|
| `onMount(fn)` | After the component is first rendered and inserted into the DOM |
| `onUpdate(fn)` | After every re-render (reactive signal change) |
| `onCleanup(fn)` | Before the component unmounts or before the next `onUpdate` call |
| `onDestroy(fn)` | When the component is permanently unmounted |

```tsx
import { signal, onMount, onUpdate, onCleanup } from 'velox/client';

export default function DataComponent() {
  const data = signal<any[]>([]);
  const loading = signal(true);

  onMount(async () => {
    const response = await fetch('/api/data');
    data.value = await response.json();
    loading.value = false;
  });

  onCleanup(() => {
    // abort pending requests, clear timers, etc.
  });

  return (
    <div>
      {loading.value ? <p>Loading...</p> : <ul>{data.value.map(d => <li>{d.name}</li>)}</ul>}
    </div>
  );
}
```

## Component Composition Patterns

### Higher-Order Components

```tsx
function withAuth<T extends {}>(Component: VeloxComponent<T>) {
  return function AuthGated(props: T) {
    const user = useUser();
    if (!user) return <Redirect to="/login" />;
    return <Component {...props} />;
  };
}
```

### Render Props / Function-as-Children

```tsx
interface FetcherProps<T> {
  url: string;
  render: (data: T) => VeloxNode;
}

export function Fetcher<T>({ url, render }: FetcherProps<T>) {
  // ... fetch logic
  return render(data);
}
```

## Component Library

Velox ships an optional official component library `@velox/ui` with accessible, unstyled base components. Install it separately:

```bash
npm install @velox/ui
```

```tsx
import { Button, Input, Dialog } from '@velox/ui';
```

See the [Component API](pages/api-components.md) reference for the full `defineComponent` API and advanced component patterns.
