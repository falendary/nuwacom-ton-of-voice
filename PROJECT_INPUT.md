# Project Input & Requirements History

> This file is a living record — every requirement, constraint, assumption, and piece of feedback gets logged here in chronological order. Nothing gets deleted. When something changes, a new entry explains why.

---

## Entry 001 — Initial Brief
**Source:** `Testday.pdf` (nuwacom test exercise)
**Date:** 2025-04-02
**Type:** Original requirement

### Problem Statement
AI-generated texts are generic and impersonal. They ignore brand voice, sound Americanized, and fail to reflect the linguistic nuances, tone, and forms of address that make a brand recognizable. Companies need a way to ensure AI-generated content aligns with their communication style.

### Goal
Derive a consistent tone-of-voice from existing corporate communications. Store it as a reusable "signature." Use that signature to optimize future texts so they reflect the brand's unique voice.

### Tasks specified in brief
1. Define the 5 most important tone-of-voice characteristics (tone, language style, formality level, forms of address, emotional appeal)
2. Build an analysis program (Python/TypeScript or similar) that identifies patterns in existing texts
3. Extract and store the derived characteristics in a structured form (the signature)
4. Use the signature as a prompt basis to optimize future texts

### Technical hints from brief
- Use LLMs for analysis and extraction
- NLP techniques for semantic and syntactic analysis
- Optional: small frontend + backend (NodeJS, TypeScript suggested — **we chose Django instead, rationale below**)
- OpenAI keys offered — **we chose Anthropic/Claude instead, rationale below**
- A perfectly functioning program is not expected; approach and thinking matter more

### Deviations from brief (with rationale)
| Brief suggestion | Our choice | Reason |
|---|---|---|
| NodeJS / TypeScript | Django (Python) | Python is stronger for NLP/text processing toolchain; faster to prototype REST APIs with DRF |
| OpenAI | Claude (Anthropic) | Superior instruction-following for structured JSON output; nuwacom is the client — testing their stack makes sense |

---

## Entry 002 — Initial Architecture Decisions
**Source:** Developer assumptions
**Date:** 2025-04-02
**Type:** Assumption

- **SQLite** chosen over PostgreSQL for zero-infra MVP speed. Known limitation, documented.
- **Django Admin** used for auth — no custom login UI in MVP scope.
- **Synchronous Claude calls** — no Celery/Redis task queue. Acceptable latency for a demo.
- **12,000 character truncation** per document before Claude call — prevents token overflow, keeps cost predictable.
- **5 signature characteristics** chosen with non-overlapping scopes (see PLAN.md §Feature 3 for definitions).
- **Demo data written first** — drives prompt quality and test fixture realism before any code exists.


## Entry 003 — Developer Assumptions (post-review)
**Source:** Developer
**Date:** 2025-04-02
**Type:** Assumption

- Signature JSON structure is flat (not nested) for simplicity of storage and prompt injection
- Claude model pinned to `claude-sonnet-4-6` — best balance of instruction-following and speed for MVP
- Text transformation preserves meaning and length approximately — no hard length constraint on output
- PNG OCR quality is not guaranteed; documented as known limitation, not a blocker
- No multilingual support in MVP — extraction prompt is English-only

---

