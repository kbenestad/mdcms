---
title: Internationalisation
sort: 130
section-id: guides
keywords: i18n, internationalisation, localisation, translation, locale routing, multilingual
description: Setting up internationalisation in Velox — translation files, locale routing, and pluralisation
language: en
---

# Internationalisation

Velox has built-in internationalisation (i18n) support through `@velox/i18n`. It handles locale detection, URL-based locale routing, typed translation files, and pluralisation.

## Setup

```bash
npm install @velox/i18n
```

Configure in `velox.config.ts`:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  i18n: {
    locales: ['en', 'fr', 'de', 'ja'],
    defaultLocale: 'en',
    routing: 'prefix-except-default',
    // 'prefix': all locales get a prefix (/en, /fr, /de, /ja)
    // 'prefix-except-default': default locale has no prefix
    // 'domain': different domains per locale
    messagesDir: 'messages',
  },
});
```

## Translation Files

Create a `messages/` directory at your project root:

```
messages/
├── en.json
├── fr.json
├── de.json
└── ja.json
```

Translation files use a flat or nested key structure:

```json
// messages/en.json
{
  "nav.home": "Home",
  "nav.blog": "Blog",
  "nav.about": "About",
  "home.hero.title": "Build faster with Velox",
  "home.hero.subtitle": "The TypeScript framework for the modern web",
  "home.cta": "Get started",
  "post.readMore": "Read more",
  "post.publishedOn": "Published on {date}",
  "post.comments": "{count, plural, =0{No comments} =1{1 comment} other{# comments}}",
  "auth.loginButton": "Log in",
  "auth.logoutButton": "Log out",
  "errors.notFound": "Page not found",
  "errors.serverError": "Something went wrong"
}
```

```json
// messages/fr.json
{
  "nav.home": "Accueil",
  "nav.blog": "Blog",
  "nav.about": "À propos",
  "home.hero.title": "Construisez plus vite avec Velox",
  "home.hero.subtitle": "Le framework TypeScript pour le web moderne",
  "home.cta": "Commencer",
  "post.readMore": "Lire la suite",
  "post.publishedOn": "Publié le {date}",
  "post.comments": "{count, plural, =0{Aucun commentaire} =1{1 commentaire} other{# commentaires}}",
  "auth.loginButton": "Se connecter",
  "auth.logoutButton": "Se déconnecter",
  "errors.notFound": "Page introuvable",
  "errors.serverError": "Une erreur est survenue"
}
```

## Using Translations

### In Server Blocks

```tsx
---
import { useTranslations } from 'velox/i18n';

const t = useTranslations();
const locale = useLocale().locale;
---

<main>
  <h1>{t('home.hero.title')}</h1>
  <p>{t('home.hero.subtitle')}</p>
  <a href="/docs">{t('home.cta')}</a>
</main>
```

### With Parameters

```tsx
---
const t = useTranslations();
const publishedDate = new Intl.DateTimeFormat(locale).format(post.createdAt);
---

<p>{t('post.publishedOn', { date: publishedDate })}</p>
```

### Pluralisation

Velox uses the ICU message format for pluralisation:

```typescript
t('post.comments', { count: 0 });   // "No comments"
t('post.comments', { count: 1 });   // "1 comment"
t('post.comments', { count: 42 });  // "42 comments"
```

### In Client Components

```typescript
import { useTranslations } from 'velox/i18n/client';

export default function LikeButton({ postId }: { postId: string }) {
  const t = useTranslations();
  const liked = signal(false);

  return (
    <button onClick={() => liked.value = !liked.value}>
      {liked.value ? t('post.liked') : t('post.like')}
    </button>
  );
}
```

## Locale Routing

With `routing: 'prefix-except-default'` and `defaultLocale: 'en'`:

| URL | Locale |
|-----|--------|
| `/` | `en` |
| `/about` | `en` |
| `/fr` | `fr` |
| `/fr/about` | `fr` |
| `/de/blog/my-post` | `de` |

Velox automatically generates alternate hreflang links for SEO.

## Locale Switcher Component

```tsx
import { useLocale, usePathname } from 'velox/i18n/client';

export default function LocaleSwitcher() {
  const { locale, locales } = useLocale();
  const pathname = usePathname();

  return (
    <div class="locale-switcher">
      {locales.map(loc => (
        <a
          key={loc}
          href={getLocalizedPath(pathname.value, loc)}
          class={loc === locale ? 'active' : ''}
          hreflang={loc}
        >
          {getLocaleLabel(loc)}
        </a>
      ))}
    </div>
  );
}

function getLocaleLabel(locale: string): string {
  const labels: Record<string, string> = {
    en: 'English',
    fr: 'Français',
    de: 'Deutsch',
    ja: '日本語',
  };
  return labels[locale] ?? locale;
}
```

## Domain-Based Routing

For country-specific top-level domains:

```typescript
export default defineConfig({
  i18n: {
    locales: ['en', 'fr', 'de'],
    defaultLocale: 'en',
    routing: 'domain',
    domains: {
      en: 'example.com',
      fr: 'example.fr',
      de: 'example.de',
    },
  },
});
```

## Type-Safe Translation Keys

Generate a TypeScript type for your translation keys:

```bash
npx velox i18n:generate-types
```

This creates `.velox/types/i18n.d.ts` so that `t('invalid.key')` is a compile-time error.

## RTL Languages

For right-to-left languages (Arabic, Hebrew, etc.), add the `dir` attribute dynamically:

```tsx
// layouts/default.velox
---
const { locale } = useLocale();
const isRTL = ['ar', 'he', 'fa'].includes(locale);
---

<html lang={locale} dir={isRTL ? 'rtl' : 'ltr'}>
  ...
</html>
```

## Date, Number, and Currency Formatting

Use the `Intl` APIs with the current locale:

```typescript
import { useLocale } from 'velox/i18n';

const { locale } = useLocale();

// Dates
const dateFormatter = new Intl.DateTimeFormat(locale, { dateStyle: 'long' });
const formatted = dateFormatter.format(new Date(post.createdAt));

// Currency
const priceFormatter = new Intl.NumberFormat(locale, {
  style: 'currency',
  currency: 'USD',
});
const price = priceFormatter.format(product.price);
```
