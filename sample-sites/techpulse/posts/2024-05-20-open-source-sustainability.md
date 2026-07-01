---
title: "Open Source Sustainability Crisis: Who Pays for the Infrastructure?"
created: 2024-05-20 14:00
author: Clara Winthorpe
keywords: open source, sustainability, xz backdoor, OpenSSF, Sovereign Tech Fund, funding
description: The xz backdoor incident exposed what many already knew — the open source infrastructure powering global commerce is maintained by a handful of burned-out volunteers. Who should pay for it?
---

![Open Source Infrastructure](assets/images/open-source.jpg)

In late March 2024, a lone security researcher named Andres Freund noticed something odd while investigating slow SSH logins on his Debian machine. After several hours of careful investigation, he discovered that a utility called xz — a compression library used by nearly every Linux distribution on the planet — had been deliberately backdoored by a person who had spent nearly two years systematically building trust in the project.

The attacker, who used the alias "Jia Tan," had contributed carefully to the project, built relationships with the exhausted maintainer, gradually taken on more responsibility, and ultimately introduced malicious code in a new release. Had Freund not been unusually attentive, the backdoor would have shipped in the next Debian stable release, potentially giving the attacker root access to millions of systems.

The incident was a near-miss, and near-misses have a way of clarifying structural problems. The xz backdoor was not primarily a story about one clever attacker. It was a story about a maintainer who was exhausted, burned out, and clearly being manipulated by someone who had identified the soft spot in the infrastructure of global computing. It was a story about a critical piece of software being maintained by one person, effectively alone, for years.

## The Scale of the Problem

The problem is not new, but the xz incident gave it a face. The Log4Shell vulnerability in 2021 was another crystallising moment — a critical flaw in a library maintained by a handful of volunteers and used by an enormous fraction of enterprise Java applications. The maintainers were not paid by the companies whose software depended on their work. They were volunteers.

A 2022 census by the Harvard Institute for Quantitative Social Science and the Linux Foundation found that a significant proportion of the most-depended-upon open source packages were maintained by one or two people. The most popular packages on npm and PyPI were maintained by individuals who, in many cases, had day jobs that had nothing to do with open source.

The economic pattern is easy to understand and hard to solve. Open source is a public good — software that, once created, can be used by anyone without reducing its availability to others. Public goods are chronically underprovided by markets, because the value they generate is not captured by the people who provide them. Companies that build products on top of open source software capture enormous value while contributing very little back to the infrastructure that makes it possible.

This is not a moral judgment about those companies. The incentive structure simply does not reward contribution. If you are a startup trying to survive, spending engineering time on upstream contributions is expensive and the benefit is diffuse and long-term. You take the open source library, use it, and move on.

## What Is Being Done

Several organisations have taken serious steps to address the problem, though none of them at the scale the problem requires.

**The Open Source Security Foundation (OpenSSF)** was established in 2020 under the Linux Foundation umbrella with a mission to improve the security of the open source supply chain. After Log4Shell, it received a significant injection of funding from major technology companies — $150 million pledged at a White House summit in 2022. The OpenSSF has funded important work including security reviews of critical packages, developer training, and tooling for software supply chain security. Critics argue it remains under-resourced and too focused on tooling and standards rather than directly funding maintainers.

**The Sovereign Tech Fund**, established by the German Federal Government, takes a different approach: it directly funds maintenance work on specific open source projects with demonstrated public-interest importance. The funding is structured as contracts, which means maintainers are paid for the work they do. The approach is less scalable than an industry-wide levy but more direct in its impact.

**GitHub Sponsors and Open Collective** provide mechanisms for individuals and organisations to fund open source maintainers directly. These platforms have enabled some maintainers to earn meaningful income from their work, but the amounts are rarely sufficient to make open source maintenance a full-time job for the people maintaining the most critical infrastructure.

**Corporate open source programmes** at companies like Google, Microsoft, and Red Hat fund significant open source development, but primarily on projects that serve their own strategic interests. The correlation between corporate open source investment and public infrastructure importance is imperfect.

## Three Models for a Solution

The open source sustainability problem has generated considerable debate about structural solutions. Three models receive the most serious attention.

**The infrastructure levy model** proposes requiring companies above a certain revenue threshold that derive benefit from open source software to contribute a percentage of their revenue — or their open source benefit — to a pooled fund. The pooled fund would then distribute money to projects based on dependency data and criticality scores. The model is attractive in its comprehensiveness and its alignment with the public-goods economics of open source. The challenge is implementation: who decides which projects are critical, who administers the fund, and how do you compel contribution internationally?

**The procurement mandate model** proposes requiring government and critical infrastructure organisations to demonstrate that the open source software in their supply chains is adequately funded and maintained — similar to how procurement rules already require vendors to demonstrate security practices. This creates a demand-side pressure on companies using open source software in government contracts. The weakness is scope: government procurement represents only a fraction of open source usage.

**The foundation consolidation model** argues that rather than trying to fund individual maintainers, the solution is to consolidate important open source projects under well-resourced foundations that have sustainable funding models. The Apache Software Foundation and the Linux Foundation represent versions of this model. Critics argue that not all valuable open source projects can or should become foundation projects, and that foundation governance introduces its own bureaucracy and risk.

## What the xz Incident Actually Tells Us

The xz backdoor incident tells us something important that the sustainability discussion often misses: the risk is not just that unmaintained projects become insecure through neglect. The risk is that burned-out maintainers are actively targeted by sophisticated actors who understand that exhaustion and isolation make people vulnerable to manipulation.

The person who attacked xz did not exploit a code vulnerability. They exploited a social vulnerability — a maintainer who was clearly struggling, who had been expressing burnout in public for months, and who was susceptible to the apparent helpfulness of a patient, skilled contributor. The attack required patience, social engineering, and a long-term strategy. It was a state-level or near-state-level operation targeting the weakest link in critical software infrastructure.

No amount of tooling addresses that threat directly. Only sustainable, funded maintenance — maintainers who have colleagues, who are not working alone under financial pressure, who have the time and support to be discerning about contributors — reduces that risk meaningfully.

The xz incident was a near-miss. The next one may not be.

---

*Clara Winthorpe covers open source and infrastructure at TechPulse. She contributed to documentation for two of the affected packages.*
