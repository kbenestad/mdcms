---
title: "Kubernetes Fatigue Is Real — Here's What Teams Are Doing Instead"
created: 2025-06-15 09:00
author: Clara Winthorpe
keywords: Kubernetes, k8s, platform alternatives, Fly.io, Railway, managed services, infrastructure fatigue
description: Our survey of 200 engineering teams finds growing Kubernetes fatigue. We look at who is leaving, who is staying, and what the alternatives actually look like in practice.
---

The Kubernetes enthusiasm that dominated infrastructure conversations from 2018 through 2022 has given way to something more complicated: a widespread recognition that Kubernetes is extraordinary infrastructure for a specific set of problems, and an unfortunate default solution for many problems it is not well-suited for.

Over eight weeks, TechPulse surveyed 200 engineering teams about their infrastructure choices, their experience with Kubernetes, and what they have changed or considered changing in the past 18 months. The findings suggest a market in transition — not a Kubernetes collapse, but a significant reassessment.

## The Survey Findings

Of the 200 teams surveyed, 142 were using Kubernetes at the time we spoke with them. Of those:
- 31% described themselves as "fully satisfied" with Kubernetes for their workloads
- 44% described it as "working well but resource-intensive to maintain"
- 18% described it as "more trouble than it's worth for our scale"
- 7% were "actively looking to migrate away from it"

Among the 58 teams not using Kubernetes:
- 22 had migrated off Kubernetes in the past two years
- 19 had evaluated Kubernetes and decided not to adopt it
- 17 had never seriously considered it

## Who Is Going Back to VMs

The teams that have migrated away from Kubernetes share a recognisable profile: they are typically under 30 engineers, running fewer than ten services, and they adopted Kubernetes because it was the industry default rather than because their workloads specifically required it.

"We had three microservices and six engineers and we were running Kubernetes because that's what you did," the CTO of a 20-person SaaS company told us. "We spent the equivalent of one full-time engineer's time just managing the cluster. We moved to managed VMs and a simpler deployment process and we have not looked back."

Several teams have returned to virtual machines, either managed directly through cloud providers or through platforms that provide a higher level of abstraction over VMs. The appeal is straightforwardness: a VM does what you tell it to, has a clear resource model, and does not require understanding pod scheduling, ingress controllers, persistent volume claims, and a dozen other Kubernetes-specific concepts.

The cost argument is also real. Kubernetes clusters have a minimum overhead — the control plane, the node agents, the namespace overhead — that adds up for small workloads. A small application running on a properly-sized VM is often significantly cheaper than the same application running in a Kubernetes cluster, even before you account for the engineering time.

## Managed Services: The Middle Ground

The most common "instead of Kubernetes" choice in our survey was not VMs but managed services — giving responsibility for the infrastructure to a cloud provider or a specialist platform and focusing on application code.

AWS Fargate, Google Cloud Run, and Azure Container Apps all provide container running services without requiring Kubernetes knowledge. The tradeoffs are loss of control and increased per-unit cost, but for many teams the operational simplification justifies both.

Among smaller and developer-first companies, Fly.io and Railway have attracted significant attention and, in some cases, meaningful migration away from both Kubernetes and AWS-native services.

## Fly.io: What the Hype Is About

Fly.io has built an infrastructure layer that runs containers close to users at a global network of data centres, with a developer experience that is genuinely simple compared to Kubernetes. Deployments happen from the command line with `fly deploy`. Machines start in seconds. Pricing is straightforward and usage-based.

The teams we spoke with that have moved to Fly.io consistently described the same thing: a dramatic reduction in infrastructure cognitive load. "I stopped spending Sunday evenings worrying about the cluster," one engineering lead said. "The infrastructure just runs."

The limitations are real. Fly.io gives you less control than Kubernetes — you cannot bring arbitrary infrastructure, the networking model is fixed, and the platform is still maturing. Several teams we spoke with noted that they had hit edge cases where Fly.io's abstraction made it difficult to do things that Kubernetes made possible, though complex.

Fly.io also had several well-publicised reliability incidents in 2023 and early 2024 that caused teams evaluating it to pause. The company has invested significantly in reliability since then, and the teams currently running production workloads on it describe good availability. But the incidents created a trust deficit that is still being rebuilt.

## Railway: The Simplest Option

Railway occupies an even simpler position than Fly.io. It is closer to a PaaS — you give it a GitHub repository and environment variables, and it figures out how to run your code. There is almost no infrastructure configuration. The target user is a developer who wants to run a backend service without any ops work.

Among the teams we spoke with, Railway is primarily used for internal tools, side projects, and small production services where engineering simplicity is the primary goal and workload characteristics are predictable and modest. It is not being seriously evaluated for large-scale, complex production workloads. It is not trying to be.

## The Teams Staying With Kubernetes — And Why

The 31% of Kubernetes teams that described themselves as fully satisfied are worth understanding. What do they have in common?

They are large enough to justify dedicated platform engineering. Every fully-satisfied team we spoke with had at least two engineers whose primary focus was platform and infrastructure. This creates a different experience: Kubernetes is complicated to maintain, but if someone's job is maintaining it, the complexity becomes manageable.

Their workloads genuinely benefit from Kubernetes' capabilities. The teams most satisfied with Kubernetes are running workloads with heterogeneous resource requirements, complex networking, stateful services that benefit from Kubernetes-native storage, or compliance requirements that benefit from Kubernetes' audit and access control capabilities.

They have invested in abstractions above raw Kubernetes. Every satisfied Kubernetes team we spoke with had built internal tooling or adopted a platform layer — Helm charts, Backstage, Crossplane, or an internal developer platform — that abstracted the Kubernetes complexity for application developers. They were, in effect, doing platform engineering.

## The Real Lesson

The lesson of the Kubernetes fatigue phenomenon is not that Kubernetes is a bad technology. It is an extraordinary piece of software that has enabled an entire generation of complex distributed systems. The lesson is about fit: Kubernetes is the right tool for a specific class of problems, and it was adopted as the universal solution for all problems, which it is not.

The teams most satisfied with Kubernetes know exactly why they are using it. The teams most frustrated with it are often teams that adopted it because everyone else was doing so, without asking whether the tradeoffs made sense for their scale, team size, and workload characteristics.

The infrastructure market is slowly recalibrating toward fit-for-purpose choices. That recalibration is healthy.

---

*Clara Winthorpe covers infrastructure, open source, and DevOps at TechPulse. She surveyed 200 engineering teams between March and May 2025.*
