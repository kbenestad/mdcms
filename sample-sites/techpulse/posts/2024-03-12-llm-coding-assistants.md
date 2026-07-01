---
title: "The Real Impact of AI Coding Assistants on Developer Productivity"
created: 2024-03-12 09:00
author: Raj Patel
keywords: AI coding assistants, GitHub Copilot, developer productivity, code quality, security vulnerabilities
description: A study of 500 developers reveals a 40% productivity gain from AI coding tools — but the picture is more complicated than that number suggests.
---

![AI Coding Tools in Practice](assets/images/ai-coding.jpg)

The claim had been circulating for months before anyone tested it rigorously: AI coding assistants make developers significantly more productive. GitHub cited a 55% productivity increase in one controlled study. Other vendors published numbers ranging from 30% to 70%. The figures were eye-catching enough that engineering managers had started asking their teams to adopt tools they barely understood.

We wanted to know what the numbers looked like in practice, with real codebases and real deadlines. Over three months, TechPulse conducted a study with 500 developers across 40 companies — from eight-person startups to engineering organisations with several thousand employees. The headline number is real: developers using AI coding assistants completed assigned tasks approximately 40% faster than developers working without them. But the story behind that number is considerably more complicated.

## What the 40% Number Actually Measures

The productivity gain is real, but it is narrow. The tasks where AI assistants shine are tasks that involve writing code that follows patterns the model has seen many times: implementing a standard CRUD endpoint, writing unit tests for a function, converting data between formats, generating boilerplate for a new module. These are real tasks that occupy real developer time, and getting through them faster is genuinely valuable.

The 40% improvement collapses significantly on tasks that require architectural reasoning, debugging complex interactions, or working with novel or unusual codebases. Several engineering leads we interviewed noted that junior developers using AI assistance were completing simple tasks quickly but struggling more with integration and debugging — skills that develop partly through the friction of writing code by hand.

"The tool makes the easy stuff faster," one senior engineer at a fintech company told us. "The hard stuff is still hard. Sometimes it's harder, because the AI has generated three hundred lines of plausible-looking code that has subtle bugs in it, and now I have to find them."

## Code Quality Concerns

Every organisation in our study that had been using AI coding tools for more than six months reported concerns about code quality. The pattern was consistent: AI-generated code tends to pass automated tests (partly because AI tools are good at writing tests to match the code they just wrote), but it tends to have more subtle architectural issues, more duplication, and higher cyclomatic complexity than code written by experienced developers from scratch.

We reviewed 3,000 pull requests across six companies that had adopted AI coding tools, comparing them against a baseline period before adoption. Code review times increased by 23% on average, and the fraction of pull requests that required significant rework before merging increased from 18% to 29%. Engineering managers who had expected AI tools to reduce code review burden found the opposite.

One particularly striking finding: AI tools generated code that cited non-existent library functions in approximately 4% of completions — a phenomenon the AI community calls "hallucination" but that engineers working with production code describe less charitably. In most cases this was caught during compilation or testing, but not always.

## Security Vulnerabilities in AI-Generated Code

The security picture is the most concerning finding in our study. A research team at Stanford published a paper in 2023 showing that developers using GitHub Copilot were more likely to introduce security vulnerabilities than developers without assistance. Our study found similar patterns.

Working with a security consultancy, we reviewed AI-generated code across fifteen repositories and identified security issues at a rate roughly 1.8x higher than the baseline codebases. The most common issues were SQL injection vulnerabilities, insecure random number generation, improper input validation, and hardcoded credentials — all classic beginner-level security errors that experienced developers have learned to avoid.

The problem is not simply that AI generates insecure code. It is that AI generates insecure code that looks plausible and confident, which is harder to catch than obviously amateurish code. Several CTOs we interviewed noted that they had tightened security review requirements after adopting AI coding tools, which partially offset the productivity gains.

"We're faster at getting to review, but review itself is more expensive," one CTO said. "The net is positive, but not as positive as the raw productivity numbers suggest."

## Developer Dependency and Skill Development

Four of the five most senior developers we interviewed — people with 15 or more years of experience — expressed concern about what AI coding tools are doing to skill development at the junior level. The concern is not luddite: all of them use the tools themselves. The concern is structural.

Learning to code involves making mistakes, finding bugs, building mental models through failure. AI tools smooth over that friction. Junior developers who use AI assistants heavily may be writing more code per hour than their predecessors, but they may also be building shallower mental models of how that code actually works. Several engineering leads reported that junior developers who had learned primarily through AI-assisted coding had difficulty debugging issues that the AI could not solve — which is to say, the hard cases.

"They can write a React component, but they don't really know what's happening inside it," one engineering manager told us. "Five years ago, a junior developer who couldn't explain what they'd written would be a red flag. Now it's become normal, and I'm not sure that's good."

## Practical Recommendations

Our recommendation for engineering organisations is neither uncritical adoption nor reflexive rejection. AI coding assistants are real productivity tools with real limitations. Used thoughtfully, they save time on repetitive tasks and reduce the cognitive cost of context-switching. Used carelessly, they create security debt and development practices that don't scale.

Specific recommendations based on our study:

**Do not remove mandatory code review.** The temptation to treat AI-generated code as more reliable than it is will cost you in the medium term.

**Invest in security review tooling.** Static analysis and SAST tools should be running on all AI-generated code, and security training should be updated to cover AI-specific vulnerability patterns.

**Think carefully about junior developer onboarding.** The productivity gains are lowest for junior developers, and the skill development concerns are highest. Consider structured periods of work without AI assistance.

**Track quality metrics, not just velocity.** If your only measurement is pull request throughput, you will optimise for throughput. Track defect rates, review times, and rework rates as well.

The 40% productivity gain is real. So are the costs. Engineering organisations that acknowledge both are better positioned to capture the benefits while managing the risks.

---

*Study methodology: 500 developers across 40 companies, surveyed December 2023 through February 2024. Task completion data collected via controlled task assignments; code quality data collected via pull request analysis with developer consent. Full methodology available on request.*
