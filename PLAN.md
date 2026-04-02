# Tone-of-Voice MVP — Project Plan

> **Context:** A ~2-hour MVP exercise for nuwacom. The goal is a working Django application that ingests brand documents, extracts a tone-of-voice signature using Claude (Anthropic), and applies that signature to rewrite arbitrary user text.

---

## Architecture Overview

```
Django (SQLite) + Claude API (Anthropic) + REST API + Django Templates UI
```

| Layer | Choice | Rationale |
|---|---|---|
| Backend | Django 4.x + SQLite | Fast to scaffold, zero infra overhead |
| LLM | Claude via Anthropic SDK | Matches test brief; superior instruction-following |
| Auth | Django Admin (built-in) | No custom UI needed for MVP |
| API Docs | drf-spectacular (Swagger/ReDoc) | Auto-generated from DRF serializers |
| Frontend | Django Templates (no JS framework) | Keeps scope tight; functional over flashy |
| Tests | Django TestCase + APITestCase | Every endpoint, action, and model covered |

---

## Build Order

> Sequence matters in a 2-hour sprint. Demo data comes **first** — it drives prompt quality, fixture realism, and manual testing from minute one.

```
Demo Data → Scaffold → Brand+Document Models → Text Extraction → Claude Service → REST API → Swagger → UI → Tests
```

| Step | Issue | Est. Time |
|---|---|---|
| 1 | Demo data (nuwacom + Apple brand files) | 15 min |
| 2 | Project scaffold + settings | 10 min |
| 3 | Brand + Document models (merged) | 10 min |
| 4 | File upload + text extraction (PDF/DOCX/TXT/PNG) | 15 min |
| 5 | Claude service: extraction + transformation | 20 min |
| 6 | REST API: CRUD + extract + transform endpoints | 20 min |
| 7 | Swagger / ReDoc | 5 min |
| 8 | Django Templates UI | 20 min |
| 9 | Unit tests | 25 min |
| — | Buffer / polish | 10 min |

---

## Core Features (MVP Scope)

### 1 — Demo Data *(done first)*

Two brand personas, 5 files each, written before any code is touched. This grounds the prompt engineering in reality rather than abstract specs.

**Brand A — Nuwacom-style** (`demo_data/nuwacom/`)
- `about.txt` — company overview paragraph
- `product_page.txt` — feature description page
- `blog_post.txt` — thought leadership, mid-length
- `press_release.txt` — new feature announcement
- `onboarding_email.txt` — welcome email to new users

*Voice profile:* professional and empowering; clarity-first SaaS language; we-inclusive; structured sentences with purposeful rhythm; rational appeal with aspirational undertone

**Brand B — Apple-style** (`demo_data/apple/`)
- `product_tagline.txt` — minimal product copy
- `website_hero.txt` — homepage hero text
- `feature_description.txt` — single feature in Apple prose
- `keynote_excerpt.txt` — scripted announcement prose
- `support_article.txt` — help content in Apple voice

*Voice profile:* minimalist and declarative; poetic brevity; present-tense confidence; never explains when it can assert; addresses the reader as an individual (*you*, never *your team*)

Formats used across both: `.txt`, `.pdf` (converted), `.docx` — covers the parser matrix.
Fixture: `demo_data/fixture.json` for `manage.py loaddata`.

---

### 2 — Document Ingestion
- Upload files: PDF, DOCX, TXT, PNG (OCR via pytesseract)
- Text extracted at upload time, stored in `Document.extracted_text`
- Documents linked to a **Brand** entity
- **Truncation:** extracted text capped at **12,000 characters** per document before sending to Claude. Prevents prompt overflow on large files; keeps API cost predictable. Truncation is logged as a warning and surfaced in API response metadata (`"truncated": true`)

---

### 3 — Tone-of-Voice Signature Extraction

Claude analyzes all extracted texts for a brand and returns a **structured JSON signature** with 5 characteristics. Each is defined below with its scope and expected output shape — so the prompt and the parser are unambiguous before a line of code is written.

| # | Characteristic | What it captures | Example output |
|---|---|---|---|
| 1 | **Tone** | Emotional register and personality of the voice | `"authoritative yet approachable — leads with clarity, never with urgency"` |
| 2 | **Sentence Rhythm** | Sentence length patterns, pacing, structural preference | `"short declaratives followed by one elaborating clause; avoids run-ons"` |
| 3 | **Formality Level** | Position on a spectrum from intimate to institutional | `"semi-formal — professional enough for B2B, human enough to avoid stiffness"` |
| 4 | **Forms of Address** | How the brand addresses its reader grammatically | `"second person singular (you / your); never 'one'; occasional we-inclusive"` |
| 5 | **Emotional Appeal** | Primary persuasion mode; rational vs. emotional axis | `"rational-first with aspirational payoff; benefits before feelings"` |

These characteristics deliberately avoid overlap:
- *Tone* → personality
- *Sentence Rhythm* → structure
- *Formality Level* → register
- *Forms of Address* → grammar
- *Emotional Appeal* → persuasion logic

Claude's extraction prompt defines each boundary explicitly to prevent bleed-through.

Signature stored as JSON in `Brand.signature`. Re-extraction overwrites the previous value. The response always includes `"previous_signature_existed": true/false` so callers know whether data was replaced.

---

### 4 — Text Transformation
- User submits text via UI or API
- Claude rewrites it applying the stored signature characteristics
- Returns: original text, transformed text, signature used, character counts
- Guard: returns `400` if no signature exists yet for the brand

---

### 5 — REST API
- Full CRUD on Brands and Documents
- `POST /api/brands/{id}/extract/` — trigger extraction
- `POST /api/brands/{id}/transform/` — transform text
- All responses in consistent JSON envelope
- See [`ENDPOINTS.md`](./ENDPOINTS.md) for full payload reference

---

### 6 — Swagger / ReDoc
- Auto-generated at `/api/schema/swagger-ui/` and `/api/schema/redoc/`
- Custom action endpoints annotated with `@extend_schema`

---

### 7 — Frontend (Templates)
- Document upload form with **Django messages framework** for feedback (success / error states — never silent)
- Signature viewer per brand (rendered from stored JSON, characteristic by characteristic)
- Chatbox-style UI: paste text → transformed result appears below input
- Base template with nav between brands

---

### 8 — Unit Tests
- Models, serializers, views, Claude service layer
- Anthropic client mocked — no live API calls, no cost in CI
- Text extraction tested with real fixture files from `demo_data/`
- Target: >90% coverage

---

## Intended Limitations

These are **known constraints** accepted for MVP speed, not oversights:

| Limitation | Detail |
|---|---|
| No authentication UI | Django Admin only; API endpoints unprotected |
| No production security hardening | `DEBUG=True`; `ALLOWED_HOSTS` loaded from `.env`, not hardcoded |
| SQLite only | No connection pooling; not safe for concurrent writes |
| Synchronous Claude calls | No task queue; long extractions block the HTTP request |
| No file storage service | Files written to `MEDIA_ROOT` on local disk |
| No streaming responses | Claude output returned in full after completion |
| Basic OCR | pytesseract quality depends on image resolution |
| Single-language | No i18n; extraction prompt is English-only |
| No rate limiting | No abuse protection on API endpoints |
| Signature overwrites | Re-extraction replaces previous; response flags `previous_signature_existed` |
| Document truncation | Extracted text capped at 12,000 chars/document before Claude call |

---

## Next Steps (Post-MVP)

Deliberately excluded to keep scope to ~2 hours — prioritized for next iteration:

1. **Decoupled Frontend** — React or Vue SPA consuming the REST API
2. **PostgreSQL** — replace SQLite; add connection pooling
3. **Docker / Docker Compose** — containerize app + DB + worker
4. **Celery + Redis** — async signature extraction; WebSocket progress updates
5. **JWT Auth** — token-based auth for API consumers
6. **Signature Versioning** — full history of extractions per brand with diff view
7. **Multi-document Aggregation** — weighted extraction across documents by recency or type
8. **Streaming Transform** — stream Claude output token-by-token to frontend
9. **Multilingual Support** — signature extraction and transformation in non-English documents
10. **Fine-grained Permissions** — multi-tenant workspace support (nuwacom-style)
11. **CI/CD Pipeline** — GitHub Actions: lint, test, coverage gate, deploy

---

## Issues → GitHub Mapping

| # | Issue Title | Change from v1 | Reference |
|---|---|---|---|
| 1 | Demo data: nuwacom-style + Apple-style brand files | ⬆️ Promoted from #11 | PLAN.md §Feature 1 |
| 2 | Project scaffold: Django + SQLite + settings | unchanged | PLAN.md §Architecture |
| 3 | Brand + Document models (merged) | 🔀 Merged old #3 + #4 | PLAN.md §Feature 3 |
| 4 | File upload + text extraction (PDF/DOCX/TXT/PNG) | was #2 | PLAN.md §Feature 2 |
| 5 | Claude service: extraction + transformation | 🔀 Merged old #3 + #5 | PLAN.md §Feature 3, 4 |
| 6 | REST API: Brands + Documents CRUD | was #5 | PLAN.md §Feature 5 |
| 7 | REST API: extract endpoint | was #6 | PLAN.md §Feature 5 |
| 8 | REST API: transform endpoint | was #7 | PLAN.md §Feature 5 |
| 9 | Swagger / ReDoc integration | was #8 | PLAN.md §Feature 6 |
| 10 | Django Templates UI: upload + chatbox | was #9 | PLAN.md §Feature 7 |
| 11 | Unit tests: full coverage | was #10 | PLAN.md §Feature 8 |
| 12 | README: install, run, access | unchanged | README.md |

---

## Dependencies

| Package | Notes |
|---|---|
| `django` | 4.x |
| `djangorestframework` | REST API |
| `drf-spectacular` | Swagger / ReDoc |
| `anthropic` | Claude SDK |
| `python-docx` | DOCX extraction |
| `pypdf` | PDF extraction — **not** `pypdf2` (deprecated) |
| `pytesseract` + `pillow` | PNG OCR |
| `python-dotenv` | `.env` loading |
| `coverage` | Test coverage reporting |

---

## Related Files

- [`README.md`](./README.md) — installation and local run guide
- [`ENDPOINTS.md`](./ENDPOINTS.md) — full API payload and response reference
- GitHub Issues — one per row in the mapping table above
