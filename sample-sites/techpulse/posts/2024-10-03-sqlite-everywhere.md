---
title: "The SQLite Revolution: How a 25-Year-Old Database Took Over the Cloud"
created: 2024-10-03 09:00
author: Raj Patel
keywords: SQLite, Cloudflare D1, Turso, libSQL, edge computing, databases, cloud
description: SQLite was designed for embedded systems. Somehow it has become the database of choice for the edge computing era. Here is why, and what its limitations mean for the future.
---

SQLite was created by D. Richard Hipp in 2000 for use on guided missile destroyers, where the alternative — a server-based database — was impractical on a ship. It is a library, not a server: the database is a single file, the query engine lives in your process, and there is no network connection to manage. For 24 years, SQLite was the database in your phone, your browser, and your laptop — the invisible infrastructure of the device world.

Then the cloud industry discovered it.

In the past two years, SQLite has become the unexpected centrepiece of a new wave of database services, edge computing platforms, and developer tools. Cloudflare D1 runs SQLite at the edge. Turso has built a distributed SQLite service with a fork of the engine. The authors of libSQL, a fork of SQLite that supports extensions and replication, have raised significant venture funding. Bun, the JavaScript runtime, uses SQLite as its built-in database. The pattern is everywhere: developers and platforms are choosing SQLite for its simplicity, reliability, and the extraordinary density of its feature-to-complexity ratio.

## Why Edge Computing Loves SQLite

The reason SQLite works so well for edge computing comes down to three properties: it is an in-process library, it has no network overhead, and it produces a single portable file.

Edge computing workloads run in small, short-lived execution environments — Cloudflare Workers, Deno Deploy, Fastly Compute, and similar platforms that spin up code close to users to reduce latency. These environments have a fundamental problem with traditional databases: you cannot maintain a persistent connection to a remote database if your process might be running in Johannesburg one moment and São Paulo the next. Connection pooling becomes complex, latency becomes unpredictable, and the network hop adds overhead that defeats the purpose of edge execution.

SQLite sidesteps this problem by eliminating the network entirely. The database lives in the same process as the code, queries run at memory speed, and the whole thing can be replicated to multiple edge locations as a file. This is the insight that Cloudflare's D1 team had: if you can replicate a SQLite file efficiently to hundreds of edge locations, you get a globally distributed database with very low read latency and the simplicity of a single-file store.

## The Cloudflare D1 Architecture

Cloudflare announced D1 — its edge database service built on SQLite — in 2022, initially in beta. By 2024 it had moved to general availability and was handling a significant fraction of Workers deployments that needed persistence.

The architectural approach is worth understanding. Each D1 database is a SQLite file. Writes are processed by a primary SQLite instance running in a datacenter. Reads can be served from read replicas — copies of the SQLite file — that are distributed close to users at Cloudflare's edge locations. Replication uses a write-ahead log that is forwarded from the primary to replicas.

The tradeoffs are real but manageable for many use cases. Read-after-write consistency is eventually consistent: if you write data and immediately read it from a different edge location, you might get stale data. The replication lag is typically measured in milliseconds for nearby regions and hundreds of milliseconds for distant ones. For most web application workloads — displaying content, user profiles, product catalogues — this is acceptable. For workloads that require strong consistency (financial transactions, inventory management, anything where reading stale data causes real problems), it is not.

## Turso and the libSQL Fork

Turso occupies an interesting position in the SQLite ecosystem. They have built a distributed SQLite service, but they have also funded the development of libSQL — an open-source fork of SQLite that adds features the original SQLite project has declined to include: replication support, server mode, and extension APIs.

The SQLite project, under Hipp's stewardship, has been notably conservative about expanding the library's scope. The original design philosophy — a simple, reliable, self-contained library — has been maintained with unusual discipline. Hipp's view is that SQLite should do one thing extremely well and not try to become something it was not designed to be.

libSQL takes the opposite view: take SQLite's quality and battle-tested storage engine and add the capabilities needed for modern cloud deployments. The extension APIs in libSQL are particularly interesting — they allow embedding vector search, full-text search, and other capabilities as loadable extensions rather than baked-in features.

Turso raised $32 million in a Series A in 2024, which gives some indication of investor confidence in the approach. Whether libSQL becomes a sustainable open-source project with genuine community support, or whether it remains primarily a Turso-maintained fork, remains to be seen. The tension between the commercial interests of a funded startup and the maintenance of a genuinely open project is a familiar one.

## Comparison with PlanetScale

PlanetScale, which built a developer-friendly MySQL-as-a-service with branching and schema migration features, was the darling of the previous wave of developer database tools. It announced a pricing change in 2024 that eliminated its free tier and caused significant developer backlash, followed by a reversal. The episode illustrated both the strength of developer affection for the product and the difficulty of finding sustainable business models in developer infrastructure.

SQLite-based services have a structural advantage in this comparison: the cost basis for running SQLite at the edge is lower than running a full MySQL-compatible distributed database. This gives SQLite platforms more flexibility in pricing, which is a meaningful competitive advantage in a market where developer adoption depends heavily on having a workable free tier.

The more fundamental question is whether the use cases overlap. PlanetScale (and MySQL generally) is better suited to applications with complex relational schemas, heavy write workloads, and strong consistency requirements. SQLite-based services are better suited to read-heavy workloads, simpler schemas, and applications where the edge latency benefit justifies the eventual consistency tradeoff.

## The Limitations Nobody Talks About Enough

SQLite's concurrency model is its most significant limitation for cloud workloads. SQLite uses file-level locking: only one write can happen at a time to a given database file. For applications with high write concurrency — many users simultaneously writing to the same database — this is a real constraint that no amount of edge distribution fully addresses.

The services built on SQLite have various mitigations: Cloudflare D1 routes all writes to a primary, Turso does similar things. But the fundamental limitation of the storage engine is that it was not designed for high-concurrency writes, and it shows. Applications that need to handle thousands of concurrent writes per second to a single logical dataset will exhaust SQLite's capabilities.

For a large class of web applications, this is not a binding constraint. Most web applications are read-heavy, and the read:write ratio for typical content-serving, e-commerce, and user-profile workloads is often 10:1 or higher. In those cases, SQLite's concurrency model is not the bottleneck.

For the workloads where it is a constraint, the answer is not SQLite-at-the-edge but a distributed, strongly consistent database — which will always come with latency and operational complexity tradeoffs that SQLite does not.

## The Surprising Thing About SQLite

The most striking thing about the SQLite story is that it is about engineering quality compounding over time. Hipp has been working on SQLite for 24 years. The project has a test suite with more than 92 million test cases. Every line of code in SQLite is tested; the test code is significantly larger than the library code. This level of investment in correctness is unusual in any software project and exceptional in an open-source library.

The result is a piece of software that developers trust completely — and that trust, it turns out, is an asset with enormous value in an industry that produces new databases at a rate that makes it impossible to develop equivalent trust in any of them quickly.

SQLite is winning not because it was designed for cloud computing but because it was designed with extraordinary care, and extraordinary care compounds.

---

*Raj Patel is TechPulse's AI and developer tools correspondent. He has been following the SQLite ecosystem since 2021.*
