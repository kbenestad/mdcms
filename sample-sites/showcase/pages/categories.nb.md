---
title: Språkvelger
sort: 240
section-id: guides
description: Slik fungerer kategorivelgeren, med den faktiske konfigurasjonen.
---

# Språkvelger

Dette er den norske varianten av denne siden — filen heter
`categories.nb.md`, mens den engelske heter `categories.md`. Ingen
frontmatter-felt kobler dem sammen; suffikset `.nb.` er hele mekanismen, og
det virker fordi `nb` er deklarert i `config.yml`.

```mdcms callout-info
message: translation
```

## Bytt tilbake

Bruk språkvelgeren i topplinjen for å gå tilbake til **English**. Prøv også
å åpne en side som *ikke* har en norsk variant — for eksempel *Callouts*
eller *Blog* — mens du står i Norsk. Fordi `visibilityifnocontent: visible`
er satt i `config.yml`, blir siden liggende i navigasjonen og viser
`pagenotfoundmessage` i stedet for å falle tilbake til engelsk innhold uten
forvarsel.

For den fullstendige, engelske gjennomgangen av `categories-*`-blokken i
`config.yml`, se den engelske varianten av denne siden.
