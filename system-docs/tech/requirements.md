# Project Requirements & Decision Log

> This document is a formal record of all requirements, decisions, assumptions, and feedback related to this project. Entries are chronological and nothing is removed — changes are added as new entries.

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
- Optional: small frontend + backend (NodeJS, TypeScript suggested)
- OpenAI keys offered
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
- **5 signature characteristics** chosen with non-overlapping scopes (defined in OVERVIEW.md).
- **Demo data written first** — drives prompt quality and test fixture realism before any code exists.

---

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

## Entry 004 — Plan Presented to Nuwacom Team
**Source:** Nuwacom team
**Date:** 2025-04-02 at 11:36
**Type:** Sign-off

Plan presented to the full team. No additional feedback, no change in requirements. Moving forward according to the proposed plan as documented in `PLAN.md`.

---

## Entry 005 — Bug Discovered in Production: Claude JSON Parsing Failure
**Source:** Manual testing during demo
**Date:** 2025-04-02
**Type:** Bug report

**Symptom:** Clicking "Extract Signature" returned: `Claude API error: Claude returned malformed JSON: Expecting value: line 1 column 1 (char 0)`

**Root cause:** Claude occasionally wraps its JSON response in markdown code fences (` ```json ... ``` `) despite explicit system prompt instructions not to. The parser received the raw fence instead of valid JSON.

**Fix:** Added `_strip_code_fence()` helper in `core/services/claude.py` to strip fences before parsing. Added two new tests to cover plain and fenced JSON responses.

**GitHub issue:** #19
**PR:** #20 (`fix-get-signature` branch)

---

## Entry 006 — Post-MVP Code Review Findings
**Source:** Developer self-review
**Date:** 2025-04-02
**Type:** Improvement

Three issues identified after the initial implementation was complete:

1. **Duplicate upload validation** — `ALLOWED_EXTENSIONS`, `MAX_UPLOAD_BYTES`, and the MIME magic-byte map were defined separately in both `core/views.py` and `core/api_views.py`. Extracted to `core/utils.py`.
2. **Missing filename length guard** — filenames longer than 255 characters would cause a database error at save time. Guard added to `core/utils.validate_file()`.
3. **Admin field visibility** — `DocumentInline` did not show `extracted_text`; `file` and `filename` in `DocumentAdmin` were editable, risking accidental data corruption. Fixed.

**PR:** `polish` branch
