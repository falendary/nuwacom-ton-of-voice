# Tone-of-Voice — Project Overview

A Django application that learns a brand's writing style from uploaded documents and uses Claude (Anthropic) to rewrite text in that voice.

---

## What it does

1. **Upload** brand documents (PDF, DOCX, TXT, PNG)
2. **Extract** a tone-of-voice signature — Claude analyzes the documents and returns 5 structured characteristics
3. **Transform** any text — Claude rewrites it matching the brand's voice

The signature has exactly five fields:

| Field | What it captures |
|---|---|
| `tone` | Emotional register and personality |
| `sentence_rhythm` | Sentence length, pacing, structure |
| `formality_level` | Conversational → institutional spectrum |
| `forms_of_address` | How the brand addresses the reader (you / we / one) |
| `emotional_appeal` | Rational vs. emotional persuasion mode |

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Django 6 + SQLite |
| AI | Claude (`claude-sonnet-4-6`) via Anthropic SDK |
| API | Django REST Framework + drf-spectacular (Swagger/ReDoc) |
| Frontend | Django Templates (no JS framework) |
| Tests | Django TestCase — 97 tests, 100% coverage |

---

## Project structure

```
core/
  models.py          — Brand, Document
  services/
    claude.py        — all Anthropic SDK calls (nowhere else)
    extraction.py    — PDF/DOCX/TXT/PNG text extraction
  utils.py           — shared upload validation
  api_views.py       — REST API ViewSets
  views.py           — Django template views
  serializers.py
  urls.py
  admin.py
  tests/
demo_data/           — sample brand files (nuwacom + apple personas)
system-docs/         — this folder
```

---

## Running locally

```bash
cp .env.example .env        # add your ANTHROPIC_API_KEY and SECRET_KEY
venv/bin/pip install -r requirements.txt
venv/bin/python manage.py migrate
venv/bin/python manage.py loaddata demo_data/fixture.json   # optional demo data
venv/bin/python manage.py runserver
```

| URL | What's there |
|---|---|
| `http://localhost:8000/` | Upload UI |
| `http://localhost:8000/transform/` | Transform UI |
| `http://localhost:8000/api/schema/swagger-ui/` | Swagger docs |
| `http://localhost:8000/admin/` | Django admin |

---

## Key constraints (intentional MVP trade-offs)

| Constraint | Detail |
|---|---|
| No auth on API | Endpoints are open — localhost only |
| SQLite | Not safe for concurrent writes in production |
| Synchronous Claude calls | Long extractions block the HTTP thread |
| Local file storage | Files written to `MEDIA_ROOT`; lost on container restart |
| Text capped at 12,000 chars/doc | Prevents prompt overflow; flagged as `truncated: true` |

---

## Before going to production

Priority order — tackle these before any real users:

**Must have**
- [ ] Gunicorn + Nginx (replace `runserver`)
- [ ] Docker + docker-compose
- [ ] PostgreSQL (replace SQLite)
- [ ] Django security settings (`DEBUG=False`, HSTS, secure cookies)
- [ ] API authentication — JWT or SSO (see `STEPS_TO_PRODUCTION.md`)
- [ ] Object storage for uploads (S3 or equivalent)
- [ ] Sentry error tracking
- [ ] Health check endpoints
- [ ] GitHub Actions CI (lint + test + coverage gate)
- [ ] PostgreSQL automated backups

**Should have**
- [ ] Celery + Redis — move Claude calls off the request thread
- [ ] API rate limiting (Claude calls cost money per request)
- [ ] Structured logging
- [ ] CORS + CSRF configuration for a decoupled frontend

See [`STEPS_TO_PRODUCTION.md`](../STEPS_TO_PRODUCTION.md) for the full checklist with implementation details.

---

## Demo data

Two brand personas are included for local testing:

- `demo_data/nuwacom/` — professional B2B SaaS voice; clarity-first, empowering, semi-formal
- `demo_data/apple/` — minimalist, declarative; poetic brevity; never explains when it can assert

Load with `manage.py loaddata demo_data/fixture.json` or upload files manually via the UI.
