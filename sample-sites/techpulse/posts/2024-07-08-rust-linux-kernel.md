---
title: "Rust in the Linux Kernel: One Year Later"
created: 2024-07-08 10:30
author: Clara Winthorpe
keywords: Rust, Linux kernel, kernel drivers, systems programming, memory safety, Linus Torvalds
description: One year after the first Rust code landed in the Linux kernel, we assess what has merged, how developers have received it, and what the safety improvements look like in practice.
---

When Linus Torvalds merged the initial Rust infrastructure into Linux 6.1 in December 2022, it marked the first time in the kernel's history that a second programming language had been accepted as a peer to C. The decision was not without controversy — some longtime kernel developers questioned the choice, the timeline, and the claimed benefits. Now, roughly eighteen months later, there is enough real-world experience to make a meaningful assessment.

## What Has Actually Merged

The scope of Rust in the kernel as of mid-2024 is narrower than some coverage has suggested, but it is growing. The initial merge provided the infrastructure: the Rust toolchain integration, the core abstractions over kernel primitives, and the `rust/` directory in the kernel source tree. Actual Rust drivers and subsystems have followed more gradually.

The most significant Rust code in the mainline kernel at the time of writing is in the device driver space. The Nova GPU driver — an open-source, Rust-based driver for NVIDIA hardware — was merged in 6.9 after an extensive review period. Several other drivers have merged or are in active review, primarily in the filesystem and networking subsystems where memory safety is most critical.

Miguel Ojeda, who has led the Rust-for-Linux initiative, provided us with current numbers: as of Linux 6.9, there are approximately 31,000 lines of Rust code in the kernel tree, compared to roughly 27 million lines of C. The Rust code represents about 0.1% of the total, but the trajectory is consistently upward. The rate of Rust submissions has increased with each kernel release cycle.

## Developer Reception Has Warmed, Slowly

Early reactions from kernel developers ranged from enthusiastic to hostile. The hostility has softened, though not universally. The most prominent dissenter, Linus's statement that he considered Rust "a nice toy language" has evolved significantly over time — he has become a more cautious but genuine supporter, provided the Rust code meets the same bar as the C code.

"I don't care what language you write in," Torvalds told a kernel developer conference audience in 2023. "I care that the code is correct, maintainable, and doesn't break anything. Rust can be all of those things. It can also be none of those things. That's a property of the code, not the language."

Several kernel maintainers we interviewed noted that the quality of Rust submissions has been high. "The people doing Rust kernel work are motivated and careful," said one subsystem maintainer who asked not to be named. "The code I've reviewed has been well-thought-out. My concern is the long-term: who maintains this in five years when the novelty wears off and you need someone to do boring debugging at 2am?"

The concern about maintainer depth is legitimate. The pool of developers who can write kernel C is large; the pool who can write kernel Rust is currently much smaller. This limits the reviewers available for Rust patches and creates bus-factor risk in subsystems that go Rust-first.

## Measuring Safety Improvements

The central claim for Rust in the kernel is safety: Rust's ownership and borrowing system prevents entire classes of memory safety bugs — use-after-free, double-free, data races — that have historically been responsible for a large fraction of kernel security vulnerabilities.

Measuring this benefit is difficult, because the Rust code is new and has not yet accumulated the years of production exposure needed to generate statistical safety data. What the data does show is that approximately 65-70% of security vulnerabilities in the Linux kernel over the past decade have been memory-safety bugs — buffer overflows, use-after-free errors, and similar issues that the Rust type system prevents at compile time.

In theory, subsystems written in Rust should not produce this class of vulnerability. In practice, there are caveats. Rust kernel code must frequently use `unsafe` blocks to interact with the C kernel primitives that the Rust code is wrapping. The safety properties hold within the Rust code, but the boundary between Rust and C requires careful handling. Early reviews of kernel Rust code identified several instances where `unsafe` blocks were more expansive than necessary, providing less isolation benefit than the code appeared to offer.

The longer-term benefit will accrue as more critical code is written in Rust from scratch — code that can maintain Rust's safety invariants more completely. This is a decade-long project, not a near-term transformation.

## The C Developers' Perspective

We spoke at length with several kernel developers who remain skeptical, not of Rust in principle, but of the pace and scope of adoption. The concern is not primarily technical; it is ecosystem.

"The kernel has thirty years of tooling, documentation, and institutional knowledge built around C," one experienced kernel developer told us. "A new contributor who wants to understand a C subsystem can find tutorials, can read the same documentation generations of contributors have read, can use the same debugging tools. For Rust kernel work, they're much more on their own."

There is also a practical concern about Rust's evolution. The Rust language and compiler change more rapidly than C, and the kernel currently requires a minimum Rust version that is pinned for each kernel release. Managing the Rust toolchain requirement across the long support periods that enterprise Linux distributions depend on is not a solved problem.

## What Comes Next

The near-term roadmap for Rust in the kernel is focused on two areas. First, expanding the abstractions library — the safe Rust wrappers over kernel C primitives — to cover more of the kernel API surface. Currently, writing Rust drivers for certain subsystems requires writing `unsafe` C-interface code that should eventually be handled by the abstractions layer. Second, the Nova driver and a small number of other ambitious Rust kernel projects will serve as test cases for whether Rust is viable for large, complex kernel subsystems or only for simpler, self-contained drivers.

The longer-term trajectory depends on whether the generation of developers who grew up with Rust enters kernel development in significant numbers. If they do, Rust's share of the kernel will grow organically. If kernel development remains primarily the province of experienced C programmers, Rust will remain a promising experiment in a niche.

Given the sustained trajectory of the past year and a half, the former looks more likely than the latter.

---

*Clara Winthorpe covers open source and infrastructure. She has been following Rust-for-Linux since the project's early days.*
