Here are all 9 issue descriptions, ready to copy one by one into GitHub.

---

## Issue 1 — Demo Data (nuwacom + Apple brand files)
**Estimate:** 15 min
**Branch:** `feature/1-demo-data`

### What & Why
Before a single line of code is written, we need realistic brand text samples. These files are the raw material that Claude will analyze — if they're generic, the extracted signature will be generic too. Writing them first also means we have real test fixtures from day one instead of lorem ipsum.

### What to deliver
Two brand personas, 5 text files each, placed in `demo_data/nuwacom/` and `demo_data/apple/`. Convert at least 2 files to `.pdf` and `.docx` to exercise the full parser matrix later.

**Nuwacom-style** — professional, clarity-first SaaS language. We-inclusive. Structured sentences. Rational appeal with an aspirational undertone. Think: product page, onboarding email, thought leadership blog post, press release, company overview.

**Apple-style** — minimalist, declarative, present-tense confidence. Poetic brevity. Addresses the reader as *you* individually, never *your team*. Think: homepage hero, product tagline, keynote excerpt, feature description, support article.

Also deliver a `demo_data/fixture.json` so the data can be loaded with `manage.py loaddata`.

### Definition of Done
- [ ] 10 files exist across both brand folders (`demo_data/nuwacom/` × 5, `demo_data/apple/` × 5)
- [ ] At least 2 files are in `.pdf` or `.docx` format (not just `.txt`)
- [ ] Each file contains at least 3 paragraphs of realistic brand-voice content (no placeholder text)
- [ ] `demo_data/fixture.json` loads cleanly via `manage.py loaddata` with no errors
- [ ] PR reviewed and merged into `main`

### Known Limitations
- Content is hand-written and fictional — it approximates the brand voice, it does not come from real nuwacom or Apple communications
- Apple-style files must not reproduce any real Apple copy (copyright)

---

## Issue 2 — Project Scaffold + Settings
**Estimate:** 10 min
**Branch:** `feature/2-scaffold`

### What & Why
The skeleton everything else builds on. Gets the project running locally with the correct dependencies, environment variable structure, and URL wiring — so every subsequent issue starts from a clean, working base.

### What to deliver
A runnable Django project with one app (`core`), a `requirements.txt` with all dependencies pinned, a `.env.example` with every required variable documented, and a `settings.py` that reads all sensitive values from the environment — nothing hardcoded.

**Dependencies to include:**
`django`, `djangorestframework`, `drf-spectacular`, `anthropic`, `python-docx`, `pypdf` *(not pypdf2 — it's deprecated)*, `pytesseract`, `pillow`, `python-dotenv`, `coverage`

**Settings checklist:**
- `SECRET_KEY` from env
- `DEBUG` from env (default `True` locally)
- `ALLOWED_HOSTS` from env — not hardcoded as `['*']`
- `MEDIA_ROOT` configured for file uploads
- `INSTALLED_APPS` includes `core`, `rest_framework`, `drf_spectacular`
- `REST_FRAMEWORK` default settings block present

### Definition of Done
- [ ] `python manage.py runserver` starts with no errors on a clean clone
- [ ] `python manage.py migrate` runs cleanly (even with empty migrations)
- [ ] `.env.example` documents every variable the app expects
- [ ] No secrets or real values committed to the repository
- [ ] `requirements.txt` is pinned (specific versions, not `>=`)
- [ ] PR reviewed and merged into `main`

### Known Limitations
- SQLite is used instead of PostgreSQL — intentional for MVP speed, documented in `STEPS_TO_PRODUCTION.md`
- No custom authentication UI — Django Admin only
- `DEBUG=True` is the local default — never deploy with this value

---

## Issue 3 — Brand + Document Models (merged)
**Estimate:** 10 min
**Branch:** `feature/3-models`

### What & Why
The two core data entities. They're always created together in the same sitting — keeping them in one issue avoids artificial parallelism and one unnecessary PR.

**Brand** represents a company whose voice we're analyzing. It holds the extracted signature as a JSON blob once extraction has been run.

**Document** represents a single uploaded file belonging to a Brand. Text is extracted at upload time and stored here — Claude never reads the raw file, only `extracted_text`.

### What to deliver

**Brand model fields:**
- `name` — CharField
- `description` — TextField (optional context for humans, not used by Claude)
- `signature` — JSONField, nullable — stores the 5 extracted characteristics
- `created_at` — DateTimeField, auto

**Document model fields:**
- `brand` — ForeignKey to Brand, cascade delete
- `file` — FileField (stored in `MEDIA_ROOT`)
- `filename` — CharField (original name, stored separately for display)
- `file_type` — CharField (`pdf`, `docx`, `txt`, `png`)
- `extracted_text` — TextField — plain text extracted at upload time
- `truncated` — BooleanField — `True` if text was cut at 12,000 chars
- `uploaded_at` — DateTimeField, auto

Both models registered in Django Admin. Brand admin shows Documents as an inline.

### Definition of Done
- [ ] Both models exist in `core/models.py`
- [ ] `makemigrations` and `migrate` run cleanly
- [ ] Both registered in `core/admin.py`; Brand shows Documents inline
- [ ] `__str__` implemented on both (returns name / filename)
- [ ] Basic model unit tests pass (create, retrieve, cascade delete)
- [ ] PR reviewed and merged into `main`

### Known Limitations
- `signature` JSONField overwrites completely on re-extraction — no versioning in MVP (tracked in `STEPS_TO_PRODUCTION.md`)
- Files stored on local disk — no cloud storage in MVP

---

## Issue 4 — File Upload + Text Extraction (PDF, DOCX, TXT, PNG)
**Estimate:** 15 min
**Branch:** `feature/4-extraction`

### What & Why
When a document is uploaded, we need its contents as plain text — that's what gets sent to Claude. This issue builds the extraction layer: a service that accepts a file and returns a string, regardless of format.

This runs at upload time and stores the result in `Document.extracted_text`. Claude never touches the raw file.

### What to deliver

A `core/services/extraction.py` module with a single public function:

```python
def extract_text(file, file_type: str) -> tuple[str, bool]:
    """Returns (extracted_text, was_truncated)"""
```

**Parser matrix:**
- `.txt` → plain read, UTF-8
- `.pdf` → `pypdf` (PdfReader)
- `.docx` → `python-docx` (paragraph join)
- `.png` → `pytesseract.image_to_string` via Pillow

**Truncation:** all output capped at **12,000 characters**. If the extracted text exceeds this, trim it and return `was_truncated=True`. This gets stored in `Document.truncated` and surfaced in API responses. Log a warning when truncation occurs.

**Error handling:**
- Unsupported file type → raise a `ValueError` with a clear message
- Unreadable / corrupt file → raise a `ValueError`, do not crash the request

### Definition of Done
- [ ] `extraction.py` handles all four file types
- [ ] Truncation at 12,000 chars works correctly; `was_truncated` flag returned
- [ ] Unsupported types raise `ValueError` with descriptive message
- [ ] Corrupt/empty files handled without an unhandled exception
- [ ] Unit tests cover: each file type (using fixtures from `demo_data/`), truncation trigger, unsupported type error, empty file error
- [ ] PR reviewed and merged into `main`

### Known Limitations
- PNG OCR quality depends entirely on image resolution and clarity — not guaranteed
- Extraction is synchronous and blocks the upload request — acceptable for MVP
- Only English text reliably extracted; non-Latin scripts may produce garbage via pytesseract

---

## Issue 5 — Claude Service: Extraction + Transformation
**Estimate:** 20 min
**Branch:** `feature/5-claude-service`

### What & Why
The LLM layer — the core of the whole application. Two functions, one module, one clear boundary: everything that talks to the Anthropic API lives here and nowhere else.

**Extraction** takes a list of text strings (from a brand's documents) and asks Claude to derive a structured tone-of-voice signature as JSON.

**Transformation** takes a text string and a signature dict and asks Claude to rewrite the text in that brand's voice.

### What to deliver

`core/services/claude.py` with two public functions:

```python
def extract_signature(texts: list[str]) -> dict:
    """Analyze brand document texts and return a tone-of-voice signature."""

def transform_text(text: str, signature: dict) -> str:
    """Rewrite text applying the given tone-of-voice signature."""
```

**The 5 signature characteristics — definitions to embed in the extraction prompt:**

| Key | What it captures | Must not overlap with |
|---|---|---|
| `tone` | Emotional register and personality of the voice | sentence_rhythm |
| `sentence_rhythm` | Sentence length, pacing, structural preference | tone |
| `formality_level` | Position on intimate → institutional spectrum | tone |
| `forms_of_address` | Grammatical person and pronouns used | tone |
| `emotional_appeal` | Rational vs. emotional persuasion axis | tone |

The extraction prompt must define each boundary explicitly to prevent Claude blending them together. Instruct Claude to return **only valid JSON** with exactly these 5 keys — no preamble, no markdown fences.

**Error handling:**
- Anthropic API failure → raise a `ClaudeServiceError` with the upstream message
- Malformed JSON response → raise a `ClaudeServiceError`; log the raw response
- Missing keys in response → raise a `ClaudeServiceError`

### Definition of Done
- [ ] `extract_signature()` returns a dict with exactly the 5 expected keys
- [ ] `transform_text()` returns a non-empty string
- [ ] Extraction prompt defines all 5 characteristic boundaries explicitly
- [ ] `ClaudeServiceError` raised (not a raw exception) on API failure or bad response
- [ ] Unit tests cover: successful extraction (mocked Anthropic), successful transformation (mocked), API failure, malformed JSON response, missing keys
- [ ] **No live Anthropic calls in tests** — Anthropic client mocked throughout
- [ ] PR reviewed and merged into `main`

### Known Limitations
- Synchronous calls — Claude can take 5–15 seconds; request thread blocks for this duration (async tracked in `STEPS_TO_PRODUCTION.md`)
- No retry logic on transient failures in MVP
- Extraction prompt is English-only
- Model pinned to `claude-sonnet-4-6`

---

## Issue 6 — REST API: CRUD + Extract + Transform Endpoints
**Estimate:** 20 min
**Branch:** `feature/6-api`

### What & Why
The REST API is what makes this application composable — it's how the UI talks to the backend today and how other systems could integrate tomorrow. Every action in the app must be reachable via API.

This issue covers the full surface: Brand and Document CRUD, the extraction trigger, and the transformation endpoint. See `ENDPOINTS.md` for the exact JSON payloads.

### What to deliver

**Serializers** (`core/serializers.py`):
- `BrandSerializer` — all fields; `signature` read-only from the client
- `DocumentSerializer` — all fields; `extracted_text` and `truncated` read-only

**ViewSets** (`core/api_views.py`):
- `BrandViewSet` — list, create, retrieve, partial_update, destroy
- `DocumentViewSet` — list, create, destroy — nested under brand (`/api/brands/{brand_id}/documents/`)

**Custom actions on BrandViewSet:**
- `POST /api/brands/{id}/extract/` — triggers `claude.extract_signature()`; saves to `Brand.signature`; returns `previous_signature_existed`, `documents_analyzed`, `documents_truncated`
- `POST /api/brands/{id}/transform/` — requires existing signature; calls `claude.transform_text()`; returns original, transformed, char counts, signature used

**Consistent error responses** — all errors follow `{"error": "..."}` shape.

**Guards:**
- `/extract/` with no documents → `400`
- `/transform/` with no signature → `400`
- Claude failure → `502`

### Definition of Done
- [ ] All CRUD endpoints return correct status codes and shapes (per `ENDPOINTS.md`)
- [ ] `/extract/` response includes `previous_signature_existed`, `documents_analyzed`, `documents_truncated`
- [ ] `/transform/` response includes `original`, `transformed`, `original_char_count`, `transformed_char_count`, `signature_used`
- [ ] Both guard conditions return `400` with descriptive error message
- [ ] Claude failure returns `502` (not `500`)
- [ ] All endpoints registered in `urls.py`
- [ ] API tests cover happy paths and all error conditions (Claude mocked)
- [ ] PR reviewed and merged into `main`

### Known Limitations
- No authentication on any endpoint — localhost only in MVP
- No pagination on list endpoints
- No filtering or search on brand/document lists

---

## Issue 7 — Swagger / ReDoc
**Estimate:** 5 min
**Branch:** `feature/7-swagger`

### What & Why
Auto-generated interactive documentation from `drf-spectacular`. Anyone picking up this project — or evaluating it in a demo — can explore the full API surface without reading source code.

This is a 5-minute issue only if it's done after the API is complete. Don't start it before Issue 6 is merged.

### What to deliver
- `drf-spectacular` configured in `settings.py` and `INSTALLED_APPS`
- Schema metadata set: title (`Tone-of-Voice API`), version (`0.1.0`), description (one paragraph)
- Three URLs registered in `urls.py`:
    - `GET /api/schema/` — raw OpenAPI JSON/YAML
    - `GET /api/schema/swagger-ui/` — interactive Swagger UI
    - `GET /api/schema/redoc/` — ReDoc clean view
- Custom actions (`/extract/`, `/transform/`) annotated with `@extend_schema` so their request bodies and responses appear correctly in the schema (DRF can't infer these automatically)

### Definition of Done
- [ ] `/api/schema/swagger-ui/` loads in browser with no errors
- [ ] `/api/schema/redoc/` loads in browser with no errors
- [ ] All endpoints visible in both UIs including `/extract/` and `/transform/`
- [ ] Request body and response shape for `/extract/` and `/transform/` visible in schema (not `{}`)
- [ ] PR reviewed and merged into `main`

### Known Limitations
- Authentication not shown in schema (no auth in MVP)
- Schema is not versioned — a single `/api/schema/` endpoint only

---

## Issue 8 — Django Templates UI: Upload + Transform Chatbox
**Estimate:** 20 min
**Branch:** `feature/8-ui`

### What & Why
A minimal browser UI so the application can be demoed without Swagger or curl. Two views: one for managing documents, one for transforming text. No JavaScript framework — Django templates and a single stylesheet.

### What to deliver

**Base template** (`core/templates/base.html`):
- Nav with links to Upload and Transform views
- Django messages block — success and error banners rendered here, used everywhere

**Upload view** (`/`) — `upload.html`:
- Brand selector dropdown
- File upload form (accepts `.pdf`, `.docx`, `.txt`, `.png`)
- On success: Django messages flash "Document uploaded and text extracted" — **never silent**
- On error: Django messages flash the specific error (unsupported type, unreadable file)
- List of documents already uploaded for the selected brand, each with a delete button
- Button to trigger extraction for the brand — flashes result (signature extracted / already existed and overwritten)

**Transform view** (`/transform/`) — `transform.html`:
- Brand selector dropdown
- Textarea for input text
- Submit button
- Result panel: original text on the left, transformed text on the right
- If no signature exists for the selected brand: clear inline prompt to run extraction first
- Show the 5 signature characteristics used (rendered from the JSON, one per line)

**Stylesheet** — minimal, single file, no framework. Readable, not impressive.

### Definition of Done
- [ ] Both views render with no template errors
- [ ] File upload shows Django message on success and on error — no silent failures
- [ ] Extraction trigger shows result via Django message
- [ ] Transform view shows both original and transformed text side by side
- [ ] "No signature yet" state handled gracefully (not a 500)
- [ ] Works end-to-end with demo data loaded
- [ ] PR reviewed and merged into `main`

### Known Limitations
- No JavaScript — page reloads on every action; no real-time feedback
- No streaming of Claude output — user waits for full response before anything appears
- No mobile optimization
- Minimal styling — functional, not production-grade UI

---

## Issue 9 — Unit Tests: Full Coverage
**Estimate:** 25 min
**Branch:** `feature/9-tests`

### What & Why
Every model, serializer, endpoint, and service function needs a test. Tests must be fast and free — meaning no live Claude calls, no real file parsing where fixtures can do the job. The Anthropic client is mocked throughout.

This issue is done last but the test structure should be set up early. It's easier to write tests for code you just wrote than for code written two weeks ago.

### What to deliver

**`core/tests/test_models.py`**
- Brand creation, `__str__`, signature field starts null
- Document creation, `__str__`, cascade delete when Brand deleted
- `truncated` field defaults to `False`

**`core/tests/test_extraction.py`**
- Extract text from `.txt` fixture file — returns expected string
- Extract text from `.pdf` fixture file
- Extract text from `.docx` fixture file
- Truncation: file with >12,000 chars returns exactly 12,000 chars and `was_truncated=True`
- Unsupported file type raises `ValueError`
- Empty file raises `ValueError`

**`core/tests/test_services.py`** (Anthropic client mocked)
- `extract_signature()` with valid mocked response returns dict with all 5 keys
- `extract_signature()` with malformed JSON response raises `ClaudeServiceError`
- `extract_signature()` with API failure raises `ClaudeServiceError`
- `transform_text()` with valid mocked response returns non-empty string
- `transform_text()` with API failure raises `ClaudeServiceError`

**`core/tests/test_api.py`** (Claude mocked)
- `GET /api/brands/` returns 200 and a list
- `POST /api/brands/` creates a brand
- `GET /api/brands/{id}/` returns 200; unknown id returns 404
- `PATCH /api/brands/{id}/` updates name/description
- `DELETE /api/brands/{id}/` returns 204
- `POST /api/brands/{id}/documents/` with valid file returns 201 with `truncated` field
- `POST /api/brands/{id}/documents/` with unsupported type returns 400
- `POST /api/brands/{id}/extract/` with no documents returns 400
- `POST /api/brands/{id}/extract/` success returns `previous_signature_existed`, `documents_analyzed`, `documents_truncated`
- `POST /api/brands/{id}/extract/` when signature already exists returns `previous_signature_existed: true`
- `POST /api/brands/{id}/transform/` with no signature returns 400
- `POST /api/brands/{id}/transform/` success returns `original`, `transformed`, char counts, `signature_used`
- `POST /api/brands/{id}/transform/` on Claude failure returns 502

### Definition of Done
- [ ] All test files exist and pass with `python manage.py test`
- [ ] **Zero live Anthropic API calls** in the test suite — mocked throughout
- [ ] Coverage report shows **≥ 90%** (`coverage report -m`)
- [ ] Tests run in under 30 seconds on a standard laptop
- [ ] PR reviewed and merged into `main`

### Known Limitations
- E2E tests (full browser, real Claude) are out of scope for MVP — tracked in `STEPS_TO_PRODUCTION.md`
- Load tests are out of scope for MVP — tracked in `STEPS_TO_PRODUCTION.md`
- PNG OCR tested with a clean fixture image — real-world image quality not covered