# Project Requirements

## Problem

AI-generated texts are generic and impersonal. They ignore brand voice, sound Americanized, and fail to reflect the linguistic nuances and forms of address that make a brand recognizable.

## Goal

Derive a consistent tone-of-voice from existing corporate communications. Store it as a reusable "signature." Use that signature to rewrite future texts so they reflect the brand's unique voice.

---

## What was asked for

From the original brief (`Testday.pdf`):

1. Define the 5 most important tone-of-voice characteristics
2. Build a program that identifies patterns in existing brand texts
3. Extract and store the characteristics in a structured form (the "signature")
4. Use the signature to optimize future texts

---

## Key decisions

| Topic | Choice | Reason |
|---|---|---|
| Language | Python / Django | Stronger NLP toolchain; faster REST API prototyping than NodeJS |
| AI model | Claude (`claude-sonnet-4-6`) | Superior instruction-following for structured JSON output; nuwacom uses Anthropic — testing their stack makes sense |
| Database | SQLite | Zero-infra overhead for MVP |
| Auth | Django Admin only | No custom login UI in scope |
| Task queue | None (synchronous) | Acceptable latency for a demo; Celery is the post-MVP upgrade path |

---

## The 5 signature characteristics

Defined with non-overlapping scopes so the extraction prompt is unambiguous:

| Characteristic | What it captures |
|---|---|
| `tone` | Emotional register and personality |
| `sentence_rhythm` | Sentence length, pacing, structural preference |
| `formality_level` | Position on conversational → institutional spectrum |
| `forms_of_address` | How the brand addresses the reader (you / we / one) |
| `emotional_appeal` | Rational vs. emotional persuasion mode |

---

## Assumptions

- Signature is flat JSON — no nested structure — for simple storage and prompt injection
- Text per document capped at 12,000 characters before Claude call to prevent token overflow
- Transformation preserves meaning and approximate length — no hard output length constraint
- PNG OCR quality depends on image resolution; documented limitation, not a blocker
- English only — no multilingual support in MVP

---

## What was out of scope (intentionally)

- Production security hardening
- PostgreSQL / connection pooling
- Async Claude calls (Celery + Redis)
- JWT or SSO authentication
- Multilingual support
- Streaming responses
- Signature version history

See `STEPS_TO_PRODUCTION.md` for the full post-MVP roadmap.
