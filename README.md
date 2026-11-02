# 💡 Insights — AI & Finance Intersection

## Key Learnings from 6 Weeks of LLM Evaluation

---

## 1. The "Plausible but Wrong" Problem

The most dangerous AI output in finance is not obviously wrong — it's **confidently plausible but subtly incorrect**. A response can be:
- Professionally written ✅
- Grammatically perfect ✅
- Structurally logical ✅
- Financially incorrect ❌

**Example pattern:** An LLM might correctly identify that WACC should be used as the discount rate, then miscalculate it by using pre-tax cost of debt instead of after-tax, arriving at a plausible but wrong valuation.

**Implication:** Finance AI tools require domain expert oversight, not just general quality review.

---

## 2. Regulatory Knowledge is a Hard Boundary

LLMs showed strong performance on general financial concepts but significant weakness on:
- Jurisdiction-specific regulatory details
- Recent regulatory changes (post-training cutoff)
- Nuanced compliance interpretations

**Implication:** AI in regulatory finance (compliance, audit, EU funds) needs human-in-the-loop architecture.

---

## 3. Structured Prompting Dramatically Improves Output Quality

Responses to well-structured prompts (clear context, specific question, defined format) were consistently superior to responses to vague prompts — even from the same model.

**Implication:** Prompt engineering is a critical skill for finance professionals using AI tools.

---

## 4. RLHF Quality Depends on Evaluator Expertise

The value of human feedback is directly proportional to the evaluator's domain depth. A general annotator and a finance professional with 15+ years experience will produce fundamentally different feedback signals — the latter detecting errors invisible to the former.

**Implication:** Domain-specific RLHF is essential for enterprise finance AI applications.

---

## 5. AI Augments, Doesn't Replace, Financial Reasoning

After evaluating hundreds of finance responses, the pattern is clear:
- AI excels at: structure, summarization, breadth, speed
- Humans excel at: judgment, nuance, regulatory interpretation, error detection

The optimal workflow is **human-AI collaboration**, not substitution.

---

## Professional Development Impact

This project significantly deepened my understanding of:
- How large language models reason about financial topics
- Where AI reliability breaks down in professional contexts
- How to design evaluation frameworks for AI outputs
- The intersection of financial expertise and AI development


---

## Runnable Finance AI Evaluation Portfolio

Six AI-assisted Python prototypes with synthetic fixtures, 63 unit tests, and reproducible reports:

1. [Financial Answer Evaluator](portfolio/01-financial-answer-evaluator/) — WACC, terminal value and margin checks.
2. [Evidence Auditor](portfolio/02-evidence-auditor/) — exact quotations and period/unit-aware fact validation.
3. [Evaluation Release Gate](portfolio/03-evaluation-release-gate/) — paired outcomes and quality/cost/latency gates.
4. [Budget Variance Investigation Assistant](portfolio/04-budget-variance-assistant/) — price/volume bridges and analyst review.
5. [Cash Collection Prioritization Workbench](portfolio/05-cash-collection-workbench/) — disputed/promise-aware queues and explicit cash scenarios.
6. [Supplier Proposal Comparison Assistant](portfolio/06-supplier-proposal-assistant/) — comparable contract cost, eligibility and weight sensitivity.

[Run all checks](portfolio/) · [12-project roadmap](portfolio/ROADMAP.md) · [Turkish learning guide](portfolio/LEARNING_GUIDE_TR.md)

These are local portfolio prototypes, not production systems or real model benchmarks. No confidential client data is included. Projects 04–06 include an optional model commentary adapter tested with mocked responses; no live model call has been verified. Roadmap projects 07–12 remain planned.

