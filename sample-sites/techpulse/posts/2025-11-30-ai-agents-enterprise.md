---
title: "AI Agents in the Enterprise: What Actually Works"
created: 2025-11-30 11:00
author: Maya Osei
keywords: AI agents, enterprise AI, automation, LLM agents, autonomous AI, AI guardrails
description: Case studies from five companies reveal what AI agents are reliably delivering in enterprise settings — and why autonomous decision-making remains out of reach.
---

The AI agent narrative has been one of the most persistent stories in enterprise technology for the past two years. Agents — AI systems that can autonomously execute multi-step tasks, use tools, and adapt to unexpected situations — represent the promise of AI that acts rather than just advises. Investors have deployed billions into agent companies. Enterprise technology buyers have run pilots. The results, as of late 2025, are instructive.

Over three months, TechPulse conducted detailed case study interviews with five companies that have deployed AI agents in production. We also spoke with security, legal, and compliance teams who have been asked to evaluate agent deployments. What we found is a genuine technology making real contributions in specific, bounded use cases, and a gap between that reality and the full autonomy narrative that is wider than most coverage acknowledges.

## Company One: Financial Services — Document Processing

A large financial services firm deployed AI agents for initial processing of loan application documents in late 2024. The agent receives a loan application package, extracts structured data from unstructured documents (income statements, employment letters, bank statements), identifies missing documents, and produces a structured summary for human underwriters.

The results have been positive. Processing time for the document extraction and initial structuring stage has been reduced by approximately 60%. Underwriter time previously spent on document organisation is now spent on actual underwriting decisions. Error rates in data extraction have decreased compared to the manual baseline.

The key design decision that made this work: the agent operates within a tightly constrained task scope. It extracts and structures data. It does not make lending decisions. It does not send external communications. All outputs are reviewed by a human underwriter before any action is taken. The system failed several times during the pilot — wrong extractions, missed documents, format misinterpretations — but because the human review step was mandatory, none of those failures reached customers.

"The success comes from keeping the agent in a well-defined box and having a human at the exit of that box," the technology lead told us. "When we tried expanding the scope to include initial underwriting recommendations, the failure rate was unacceptably high and the failures were not always predictable."

## Company Two: Software Development — Code Review

An enterprise software company with over 1,000 engineers deployed AI agents for an initial code review pass. The agent reviews pull requests for common issues: potential security vulnerabilities, test coverage gaps, code style violations, and straightforward logic errors. It comments directly on pull requests before human review.

The outcomes are mixed but net positive. Engineers report that the agent catches approximately 30% of the issues that human reviewers would have caught, which meaningfully reduces the time human reviewers spend on mechanical issues. The agent also catches issues that human reviewers would have missed — it is thorough in a way that humans under time pressure are not.

The failure mode is false positives. The agent comments on issues that are not actually issues at a rate that engineers find annoying but tolerable. Early versions of the system had a higher false positive rate; prompt engineering and fine-tuning on the company's specific codebase have reduced it to a level that engineers describe as "better than tolerable."

The limits of the system are clear: it identifies potential issues but the resolution of those issues remains entirely with human engineers. When the agent suggests a fix, engineers review the suggestion carefully and often reject it. The agent's code generation is treated as a starting point, not a trusted output.

## Company Three: HR — Candidate Screening

A professional services firm deployed AI agents to help with initial candidate screening for entry-level positions. The agent reviews CVs, identifies candidates that meet basic threshold criteria, and generates a structured assessment of each candidate for human recruiters.

This deployment has been the most controversial case study. The firm has observed a reduction in screening time per candidate, but they have also had to navigate significant legal and HR concern about AI decision-making in the hiring process. Several jurisdictions have enacted or are considering legislation requiring disclosure when AI is used in hiring decisions.

The practical adjustment has been to treat the agent's assessment as a search and organisation tool rather than a decision tool. It finds and structures information; it does not recommend hiring or rejection. Human recruiters review every structured assessment before any candidate communication occurs.

The firm's legal team has been the most sceptical of the deployment. "The AI optimises for patterns in historical data," their legal director noted. "Historical data reflects historical hiring decisions, which have biases. We have invested significant effort in audit frameworks to identify whether the agent is introducing or amplifying bias. We have not found evidence of it, but we have also not had the system in production long enough to have high confidence."

## Company Four: Customer Support — Tier-One Resolution

A technology company deployed AI agents to handle initial customer support queries, with the goal of resolving common issues without human intervention and escalating to human agents for complex cases.

After six months in production, the agent handles 62% of inbound queries without escalation. Customer satisfaction scores for agent-handled queries are lower than for human-handled queries, but within acceptable parameters. Escalation accuracy — the agent's ability to identify which queries need human handling — is the most important metric and has improved significantly from the initial deployment.

The failure modes are instructive. The agent handles common, well-defined problems (password resets, subscription changes, billing inquiries) very well. It handles novel or ambiguous problems poorly, and it does not reliably recognise when a problem is outside its competence. Early versions of the system would confidently provide incorrect information about product features or policies rather than escalating. This has been addressed through explicit escalation triggers and confidence thresholds, but the company's engineers described ongoing tuning work as "more labour-intensive than expected."

## Company Five: Legal — Contract Review

A law firm uses AI agents as a first-pass reviewer for standard commercial contracts. The agent reviews contracts for common issues: missing standard clauses, non-standard terms in key provisions, and potential conflicts with the client's standard positions.

Lawyers at the firm describe the agent as genuinely useful for speeding up the mechanical review of routine contracts. It does not change how they work on complex, negotiated agreements — it is used for the volume work.

The guardrails in place are significant: all agent outputs are reviewed by qualified lawyers, outputs are never provided directly to clients, and the firm does not market the AI assistance as part of its service model. "We treat it the way we treat a first-year associate's work," one senior partner said. "Review everything. Trust nothing until you've checked it. Learn to read the failure modes."

## The Consistent Findings

Across these five case studies, several consistent findings emerge:

**Successful deployments are bounded.** Every successful agent deployment we encountered operates within a tightly defined scope with explicit constraints on what the agent can do, what data it can access, and what actions it can take without human approval.

**Human review is non-negotiable for consequential outputs.** No company we spoke with had removed human review from the path to consequential decisions. The value of agents is in reducing the time humans spend on mechanical aspects of a task, not in removing humans from the loop.

**Failure modes are not always predictable.** All five deployments experienced failure modes that were not anticipated during the pilot phase. The characteristic of production AI deployment is discovering new failure modes over time, which requires ongoing monitoring and prompt/system adjustment.

**Autonomous decision-making is where all five companies drew the line.** When we asked each company what they had tried and decided not to deploy, the answers clustered around autonomous decision-making tasks — anything where the agent's output would directly trigger an action without human review. Legal liability, regulatory compliance, and customer trust concerns are cited, but underneath them is a practical concern: no one has confidence in the reliability of autonomous agent decision-making at the level needed for consequential actions.

The AI agent story is real. It is just a narrower story than the investment narrative suggests.

---

*Maya Osei conducted case study interviews between August and November 2025. Companies are anonymised; descriptions may include minor modifications to protect confidentiality.*
