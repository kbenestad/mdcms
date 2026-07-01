---
title: "Open Source AI Models in 2025: The Landscape Is More Complex Than It Seems"
created: 2025-04-28 11:00
author: Raj Patel
keywords: open source AI, Llama 3, Mistral, Gemma, open weights, AI licensing, Meta AI
description: Llama, Mistral, Gemma — the "open source AI" movement is growing fast. But what does "open" actually mean when applied to large language models, and which models are actually open?
---

The phrase "open source AI model" is used everywhere and means almost nothing consistent. When Meta releases Llama 3, they call it open source. When Mistral releases their models, they call them open source. When Google releases Gemma, they call it open source. In each case, "open source" refers to something meaningfully different, and in most cases it refers to something that the Open Source Initiative and the broader open source community would not recognise as open source in the traditional sense.

This matters for practical reasons — your ability to use, modify, and redistribute a model depends on the actual terms, not the marketing language. It matters for political reasons — if "open source AI" becomes a term that can be claimed by companies that are merely releasing weights under restricted licences, it dilutes the meaning of open source in ways that will have long-term consequences for the ecosystem. And it matters for philosophical reasons — the debate about what openness means for AI models is substantively different from the debate about what openness means for traditional software, because the artefacts involved are different.

## What "Open" Can Mean for an AI Model

Traditional open source software requires, at minimum, that the source code be available and that it can be freely used, modified, and redistributed. The Open Source Definition, maintained by the OSI, has specific criteria. Most "open source" AI models fail these criteria in multiple ways.

For an AI model, the meaningful components that could be "open" include:

**Weights** — the numerical parameters that define the model's behaviour after training. Releasing weights allows anyone to run the model and fine-tune it, but without anything else, it is analogous to releasing a compiled binary without source code.

**Training code** — the code used to train the model, including architecture definitions and training procedures. This is analogous to source code in traditional software.

**Training data** — the data the model was trained on. This is arguably the most important factor in a model's capabilities and alignment, and the most important thing that is almost never released.

**Evaluation code and data** — the benchmarks and test sets used to evaluate the model's capabilities. Needed to independently verify capability claims.

Most "open" AI models release only weights, and often with restrictive licences that prohibit commercial use above a certain scale, require attribution, prohibit certain use cases, or retain the right to revoke the licence. This is not open source in any traditional sense.

## The Models and What They Actually Release

**Meta Llama 3** (and the Llama family generally) releases weights under a custom "Meta Llama 3 Community License." The licence allows commercial use but prohibits using Llama to train other large language models (a significant restriction), requires attribution, and prohibits use by entities with more than 700 million monthly active users without a special agreement. Training code is partially available. Training data is not released.

**Mistral** releases weights for several models under Apache 2.0, which is the most genuinely open licence in the "open" AI model space. Apache 2.0 allows commercial use, modification, and redistribution without restrictions beyond attribution. Mistral does not release training code or training data for its flagship models. Their "open weights" language is more honest than "open source."

**Google Gemma** uses a custom licence that allows commercial use but prohibits certain applications (explicitly: use in weapons development, surveillance, and certain high-risk medical applications) and restricts redistribution in ways that are not compatible with OSI open source criteria. Training data and training code are not released.

**Falcon** from the Technology Innovation Institute releases weights under Apache 2.0 for most model sizes, making it one of the more genuinely open options for weights. Like other models, training data is not released.

**BLOOM** from BigScience is the closest to a genuinely open model — it was trained using a diverse coalition of researchers, the training data (ROOTS) is documented and partially available, and the model is available under a licence that is OSI-compliant in spirit if not letter.

## The Training Data Problem

The deepest issue in open source AI models is training data. A model's capabilities, biases, and failure modes are substantially determined by what it was trained on. Without access to training data, you cannot truly audit a model's behaviour, cannot understand why it fails in certain ways, and cannot replicate the training to produce a model with different properties.

There are legitimate reasons why training data is not released. Much of the text used to train large language models comes from the web and includes copyrighted material — releasing the training data would create enormous copyright exposure. Personal data collected in training sets raises privacy concerns. The compute cost of reproducing a training run from data is prohibitive for most actors.

These are real constraints, not excuses. But they mean that the most important component for understanding what a model is and why it behaves as it does is, in practice, unavailable. This is a fundamental limitation on the openness of current AI models that is unlikely to be resolved in the near term.

## Commercial Use Restrictions and Their Implications

The Llama family's restriction on using its weights to train other large language models is a significant practical constraint that is easy to miss in the licence terms. It means that the Llama models, despite being widely described as "open source," cannot be used to produce derivative foundation models. You can fine-tune Llama for a specific task; you cannot use Llama as the initialisation point for a new pretrained model.

This restriction protects Meta's competitive position — they do not want to train a model that then gets used to build a competitor — while allowing the application ecosystem to develop. It is a commercially rational choice. It is not consistent with the open source principle that anyone can use open source software as the basis for any project, including a competitive one.

## The Case for Releasing Weights Anyway

None of this is an argument that releasing weights is not valuable. It is. Weights-only releases have enabled enormous amounts of useful research, have allowed fine-tuning for specialised domains, have created an ecosystem of tools and applications, and have provided a practical alternative to API-only access for organisations with privacy requirements or latency constraints.

The argument is specifically about terminology. Calling these releases "open source" obscures the real distinctions between what is genuinely open and what is open in a more limited marketing sense. Those distinctions matter for developers making architectural decisions, for researchers studying AI, and for the policy conversations about AI regulation that increasingly hinge on what "open" means.

The OSI's ongoing work to define "Open Source AI" — a formal definition that extends their existing principles to AI systems — is an important contribution to this conversation. Their current draft requires, at minimum, that training data be documented and described (not necessarily released), that training code be released, and that weights be released under an OSI-approved licence. By these criteria, almost no current major AI model qualifies as open source.

That gap between the marketing language and the formal definition deserves more attention than it gets.

---

*Raj Patel has been following the open source AI ecosystem since the Llama 1 release. He has no financial relationship with any of the companies mentioned.*
