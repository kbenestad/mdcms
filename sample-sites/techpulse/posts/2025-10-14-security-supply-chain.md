---
title: "Software Supply Chain Security in 2025: Progress Report"
created: 2025-10-14 09:00
author: Raj Patel
keywords: software supply chain security, SBOM, sigstore, GitHub security, dependencies, enterprise security
description: Three years after the xz incident and a decade after SolarWinds, we assess how much enterprise software supply chain security has actually improved.
---

The phrase "software supply chain security" entered mainstream awareness after SolarWinds in 2020 and has been a fixture of security conference agendas and government executive orders ever since. In the years since, significant resources have been invested in improving the situation: new tooling, new standards, regulatory pressure, and corporate security programmes specifically targeting the supply chain.

It is worth asking whether it has worked.

The honest answer, based on conversations with security researchers, enterprise security teams, and the people building the tooling, is: meaningfully yes in some areas, frustratingly stagnant in others, and still dramatically under-resourced overall.

## SBOM Adoption: From Mandate to Practice

The Software Bill of Materials (SBOM) — a machine-readable inventory of the components in a software product — has moved from a security researcher wish list item to a regulatory requirement in several jurisdictions. The US government's Executive Order on cybersecurity in 2021 required federal contractors to provide SBOMs. The EU Cyber Resilience Act, which came into force in phases beginning in 2024, requires SBOMs for products sold into the European market.

Adoption among enterprises has been driven primarily by these compliance requirements. Our conversations with security teams at large enterprises suggest that SBOM generation is now routine for companies operating in regulated sectors or selling to government customers. The tooling has matured: Syft, CycloneDX, and SPDX toolchains work reliably, integrate with major CI/CD platforms, and produce SBOMs that can be ingested by vulnerability scanning tools.

The gap is in what organisations do with SBOMs once they have them. Generating an SBOM is the easy part. Ingesting SBOMs from third-party software vendors, maintaining them across complex software ecosystems, and using them for actual risk management decisions is the hard part, and that work is much less mature.

"We generate SBOMs for everything we ship," one security engineer at a large technology company told us. "But we receive SBOMs from fewer than 10% of our suppliers, and even when we do, we don't have the process to operationalise them into real risk decisions. They exist in a system and nobody looks at them."

## Sigstore and the Signing Infrastructure

Sigstore — the open source project providing signing and verification infrastructure for software artefacts — has become genuine critical infrastructure. It is now used to sign virtually all Python packages uploaded to PyPI, the npm registry has begun adopting it for provenance information, and the Go module proxy uses it for module signing.

The technical architecture is solid: Sigstore uses a public, append-only transparency log (Rekor) that allows anyone to verify that a signing event occurred and when, combined with short-lived signing certificates from Fulcio that tie signatures to verified identities (typically GitHub Actions workflows or similar OIDC-based identities). The result is a system that provides meaningful verification without requiring developers to manage long-lived private keys — a significant usability improvement over PGP-based signing.

The challenge is adoption at the consumer end. Signing artefacts is now easy; verifying signatures before using them is still a manually-configured step that most developers do not take. Defaulting verification on in package managers — so that installing an unsigned or unverified package requires an explicit opt-in — is the next step that would translate signing infrastructure into routine security practice. npm has begun moving in this direction; others are more cautious.

## GitHub Dependency Scanning: What It Catches, What It Misses

GitHub's Dependabot and the code scanning features built on CodeQL have become the most widely-deployed dependency security tooling in the industry, by virtue of being free and integrated into the platform where most open source and a significant fraction of commercial software development happens.

The effectiveness data is encouraging at the surface level: Dependabot has helped organisations patch millions of vulnerable dependencies. The catch rate for known vulnerabilities with published CVEs is high.

The limitations are important. Dependabot catches dependency versions with known CVEs. It does not catch malicious packages designed to look like legitimate ones (typosquatting), does not catch compromised legitimate packages (the xz problem), and does not analyse the supply chain of the dependencies themselves — only the direct and transitive dependency versions.

"Dependabot is extremely good at what it does and that's a real improvement," one security researcher told us. "But the attacks that actually scare me — the patient, sophisticated supply chain compromises — are exactly the ones it doesn't catch, almost by definition."

## What Enterprises Are Actually Doing

We spoke with security teams at twelve large enterprises across financial services, technology, and healthcare. The practices they described, in aggregate, suggest a sector that is significantly better than it was in 2020 but still operating below the level that the threat environment warrants.

**Practices now considered routine** (done by the majority of companies we spoke with): automated dependency scanning in CI/CD pipelines, SBOM generation for shipped software, periodic security reviews of critical open source dependencies, secrets scanning in repositories.

**Practices being adopted but not yet routine**: SBOM ingestion from suppliers, software composition analysis going beyond CVE scanning to include licence compliance and quality metrics, signing and verification of container images throughout the deployment pipeline.

**Practices still in early stages**: dependency build reproducibility verification, behavioural analysis of new package versions, automated provenance verification at package install time.

The remaining gaps centre on the sophistication of the threat model. The tooling that has been deployed broadly addresses the 2015-2019 threat model: known vulnerabilities in known packages. The current threat model includes supply chain attacks against the development and build infrastructure of trusted packages, compromised maintainer accounts, social engineering of tired maintainers (xz), and sophisticated malicious packages designed to evade static analysis.

## What Would Actually Move the Needle

The security researchers and practitioners we spoke with converge on several interventions that would have the highest impact:

**Funded maintenance of critical open source projects.** The xz incident demonstrated that the most dangerous attack vector is not technical but social. Funded, supported maintainers who have colleagues and review processes are significantly harder to compromise than exhausted individuals maintaining projects alone.

**Default verification in package managers.** Making signature verification mandatory by default — so that installing an unsigned package requires explicit user action — would create a floor of supply chain integrity without requiring developer behaviour change.

**Build reproducibility at scale.** Reproducible builds — where the same source code and build inputs always produce identical binary outputs — allow independent verification that a distributed binary corresponds to its published source. Tools for achieving reproducibility have improved, but adoption at scale remains incomplete.

**Faster CVE response infrastructure.** The time between vulnerability discovery and the publication of patches and advisories in machine-readable form remains too long. Streamlining this pipeline would allow the defensive tooling to respond faster.

The progress in software supply chain security over the past five years is real and should not be minimised. The gap between where we are and where we need to be is also real and should not be minimised.

---

*Raj Patel has covered software security and supply chain issues at TechPulse since 2022. He spoke with twelve enterprise security teams and eight independent security researchers for this article.*
