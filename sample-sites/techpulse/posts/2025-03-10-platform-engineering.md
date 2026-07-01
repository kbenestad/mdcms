---
title: "Platform Engineering Is the New DevOps — And That's Both Good and Bad"
created: 2025-03-10 14:00
author: Maya Osei
keywords: platform engineering, DevOps, internal developer platforms, CNCF, golden paths, developer experience
description: Platform engineering has become the dominant framework for thinking about internal developer infrastructure. A look at whether it is solving the right problems and what the CNCF data says.
---

Every few years, the software industry invents a new term for the cluster of practices around making developers productive in complex organisations. First there was "ops." Then DevOps. Then SRE. Now platform engineering. The question worth asking is whether the new label represents genuine progress in how we think about the problem, or whether it is primarily branding that allows the same arguments to be relitigated with a fresh vocabulary.

Having spent several months reviewing the CNCF's 2025 platform engineering report, talking to platform teams at companies of varying sizes, and reading the academic and practitioner literature, my answer is: it's some of both, and the difference matters.

## What Platform Engineering Actually Means

The CNCF's Platform Engineering Maturity Model, published in 2023 and updated in 2025, defines a platform as "a foundation of self-service APIs, tools, services, knowledge, and support that are arranged as a compelling internal product." Platform engineering is the practice of building and maintaining that foundation.

The key word in that definition is "product." Platform engineering, as a discipline, differs from traditional infrastructure or DevOps work in its explicit adoption of product thinking: the internal customers of the platform are treated as users whose experience matters, whose needs must be understood through user research and feedback loops, and whose adoption should be measured and optimised.

This framing comes with a specific set of practices: platform roadmaps that are driven by developer needs rather than just infrastructure requirements, developer experience (DevEx) metrics, golden paths that offer a recommended way to do common tasks without mandating it, and internal marketing for platform capabilities. Many organisations have infrastructure teams that do not think this way; the claim of platform engineering is that this thinking produces better outcomes.

## What the CNCF Data Shows

The CNCF surveyed 1,400 organisations for their 2025 report. The headline finding: 71% of organisations with more than 500 engineers have either implemented an internal developer platform or are actively building one, up from 55% in 2023.

The outcomes data is more interesting than the adoption data. Organisations that scored highly on the CNCF's platform maturity model reported:
- 34% reduction in time from code commit to production deployment
- 28% reduction in developer onboarding time for new team members
- 19% reduction in security incidents related to misconfiguration
- Higher scores on internal developer satisfaction surveys

These numbers look compelling, but they come with a significant caveat: the organisations that have invested heavily in platform engineering are also the organisations that invest heavily in engineering infrastructure in general. The correlation between platform maturity and deployment efficiency may partly reflect underlying investment levels rather than a causal effect of the platform engineering approach specifically.

## The Problem Platform Engineering Was Built For

To assess whether platform engineering is solving the right problems, you need to understand what it is responding to. The problem is genuine: as organisations adopt microservices, containerisation, multiple cloud environments, and complex CI/CD pipelines, the cognitive load on application developers has increased dramatically.

A developer who needs to ship a feature must now navigate: Kubernetes configuration, service mesh settings, IAM policies, observability instrumentation, security scanning requirements, deployment pipeline configuration, and an ever-growing stack of infrastructure tooling. Each of these things exists for a good reason, but in aggregate they have created a situation where many developers spend more time wrestling with infrastructure than writing application code.

Platform engineering's answer is the "golden path" — a supported, opinionated way of doing common infrastructure tasks that abstracts the complexity without removing it. Instead of every developer team reinventing CI/CD pipelines, there is a platform-provided pipeline template. Instead of every team figuring out Kubernetes manifests, there is a platform-provided deployment abstraction.

The golden path metaphor is well-chosen: it is a recommendation, not a mandate. Teams that need to deviate can deviate; they just lose the platform team's support when they do. This is more functional than either "everyone figures it out themselves" or "everyone must use the standard approach regardless of whether it fits their needs."

## The Problems Platform Engineering Creates

The problems with platform engineering are less often discussed because they tend to emerge after the implementation phase, when the platform team has already been staffed and positioned as a success.

**Platform teams become bottlenecks.** When infrastructure decisions require going through the platform team, the platform team must prioritise developer requests. If the platform team is understaffed (common) or slow-moving (also common), developers wait. The same dynamic that DevOps was invented to address — developers waiting for ops to provision infrastructure — can re-emerge if platform teams are not very careful about their operating model.

**Golden paths become golden cages.** Over time, platform teams tend to optimise their golden paths for the average case, which means they work well for common use cases and badly for edge cases. Teams with unusual requirements — high-performance computing workloads, specialised security requirements, novel architectures — find themselves fighting the platform rather than being helped by it. The cognitive overhead shifts from "figuring out Kubernetes" to "figuring out how to do what I need within the platform's assumptions."

**Platform engineering replicates without redistributing complexity.** The platform team absorbs infrastructure complexity so application teams don't have to face it directly. But the complexity does not go away — it concentrates in the platform. This is often the right tradeoff. But it means that platform team burnout and turnover is extremely costly, and that organisations are creating a new class of institutional knowledge that is hard to replace.

## What The Most Successful Implementations Look Like

The platform teams we interviewed that had the most developer satisfaction and the best outcomes shared several characteristics:

They measured developer experience systematically, using DORA metrics and DevEx surveys, and used that data to prioritise platform work. They did not assume they knew what developers needed — they asked, regularly.

They adopted a product development model including a backlog, regular prioritisation, and clear roadmaps, with application developers invited to contribute to priority setting.

They treated the platform as optional for edge cases, building escape hatches and documenting them. This reduced resistance to the platform and meant developers only fought the golden path when they had genuine reasons to.

They kept the platform team small and focused on the highest-leverage infrastructure work, resisting the tendency to expand platform scope until scope expansion was clearly justified by developer demand.

Platform engineering, done well, is genuinely valuable. Done poorly, it is DevOps complexity with a product manager and a roadmap.

---

*Maya Osei covers startups, funding, and the business of developer tools at TechPulse.*
