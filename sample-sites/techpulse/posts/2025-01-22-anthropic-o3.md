---
title: "Chain-of-Thought Models Change Everything — But Not in the Way You Think"
created: 2025-01-22 09:30
author: Raj Patel
keywords: reasoning models, chain-of-thought, o1, enterprise AI, LLM limitations, AI reasoning
description: The new generation of reasoning models that think before answering have changed what AI can do. But the change is more specific — and the limitations more persistent — than the coverage suggests.
---

The AI industry's coverage of chain-of-thought reasoning models has settled into a predictable pattern: each new release produces a wave of breathless coverage about benchmark scores, followed by a wave of critical coverage pointing out that the benchmarks are gamed, followed by both camps missing the most interesting question, which is: what do these models actually change, in practice, for the people building with them?

I have spent the past several months talking to enterprise AI teams, individual developers, and AI researchers about their experience with reasoning models — the class of models, exemplified by OpenAI's o1 series and its successors, that spend additional compute "thinking" through problems before producing an output. The picture is genuinely interesting and considerably more nuanced than either the bullish or bearish coverage suggests.

## What Changed

The core change is real and important. Prior generation language models — GPT-4, Claude 3, the mid-2024 vintage of large models — produce outputs by processing a prompt and generating a response token by token in a single pass. They are good at tasks that can be solved by pattern matching over their training distribution: writing code that follows common patterns, summarising documents, answering factual questions, translating text.

They are structurally weak at tasks that require sustained multi-step reasoning — problems where getting the right answer requires holding multiple sub-problems in working memory, checking intermediate conclusions, and revising when those conclusions turn out to be wrong. Mathematical reasoning, complex debugging, multi-constraint optimisation, and formal logic tasks all fall into this category.

Chain-of-thought reasoning models address this limitation by generating explicit reasoning steps before producing a final answer. The model, in effect, writes a scratchpad of thinking that it then uses to produce a more reliable answer. The "thinking" is itself a generated sequence, which means it can be long, exploratory, and self-correcting in ways that a single-pass generation cannot be.

The empirical improvement on reasoning tasks is real and substantial. Mathematical benchmark scores, coding competition scores, and formal reasoning task scores all improve significantly with chain-of-thought models. This is not benchmark gaming in the crude sense — the improvements generalise to novel problems of the same type.

## Where Enterprise Adoption Has Gained Traction

I spoke with AI leads at seventeen enterprises across financial services, healthcare, software development, and professional services. The common thread in successful deployments is this: chain-of-thought models are making a real difference in tasks that require complex, auditable reasoning, and they are changing little in tasks that don't.

**Code review and debugging** is the clearest success story. Multiple engineering teams reported that chain-of-thought models are meaningfully better at identifying subtle bugs, understanding complex control flow, and explaining why code is wrong in ways that help developers learn. One senior engineering manager described it as "finally getting a code review from someone who actually thinks it through rather than just pattern-matching on what they've seen before." The caveat: the thinking time means latency is higher, which matters for interactive use but less for asynchronous review workflows.

**Legal document analysis** in financial services is another genuine success. Reasoning models can work through complex contract logic, identify dependencies between clauses, and flag conflicts that earlier models missed. The combination of reasoning capability and the ability to cite specific text makes them useful for audit-trail purposes in regulated industries.

**Complex data analysis tasks** — not simple aggregations but multi-step analytical reasoning — are improving. "If I ask it to figure out why our conversion rate dropped last quarter, it can actually work through the possible explanations systematically rather than just listing things that might affect conversion," one data analyst told us.

## Where They Still Fail

The failure modes of reasoning models are different from the failure modes of their predecessors but no less real.

**Reasoning models can reason very confidently toward wrong answers.** The "thinking" process generates internal consistency, but internal consistency is not the same as correctness. I have seen reasoning models produce elaborate, coherent explanations for conclusions that were factually wrong, complete with carefully structured arguments that would require domain expertise to identify as incorrect. This is, in some ways, more dangerous than an older model that produces a wrong answer in an obviously uncertain way.

**Long-horizon task completion remains elusive.** The improvements in reasoning capability apply within a bounded context: given a well-defined problem, reasoning models are better at finding the answer. They are not significantly better at managing complex projects over time, maintaining consistency across long workflows, or autonomously completing tasks that require adapting to unexpected situations. The vision of AI agents that can work on problems for hours or days remains largely unrealised despite the capability improvements.

**Domain-specific knowledge limitations persist.** Chain-of-thought reasoning improves formal reasoning but does not substitute for domain knowledge. A reasoning model asked to analyse a clinical trial design will reason more carefully but will still make errors that a domain expert would not, because its underlying knowledge of clinical research methodology is imperfect. Reasoning models are better advisors in areas where careful thinking matters; they are not reliable substitutes for domain expertise.

**Cost and latency are real constraints.** Reasoning models consume significantly more tokens than standard models, because the thinking process itself generates output that must be processed. API costs for reasoning-heavy tasks can be 5-10x higher than equivalent tasks on standard models. For some high-value tasks this is obviously worthwhile. For high-volume, latency-sensitive applications, it changes the economics significantly.

## The Pattern That Matters

The enterprise teams making the best use of reasoning models have converged on a pattern: use them for decisions, not for generation. Standard models are still excellent for generating content — writing emails, summarising documents, producing code scaffolding. Reasoning models are worth their cost for the decision-making steps: reviewing that code, analysing that document for specific logical issues, working through a complex technical question.

The mistake made by teams that have been disappointed with reasoning models is using them as a drop-in replacement for standard models in generation tasks, where the reasoning capability provides little benefit and the cost and latency increase is pure overhead.

Chain-of-thought models have changed something real about what AI can do. They have not changed the fundamental challenge of deploying AI in production: knowing precisely what the system can and cannot do reliably, and designing your workflow so that the unreliable parts have appropriate human oversight.

---

*Raj Patel spoke with AI engineering teams at seventeen enterprise companies between October 2024 and January 2025. Companies are not named; they requested anonymity as a condition of participation.*
