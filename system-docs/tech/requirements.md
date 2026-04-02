# Requirements

Python 3.13. All packages pinned in `requirements.txt`.

## Runtime dependencies

| Package | Version | Purpose |
|---|---|---|
| `Django` | 6.0.3 | Web framework, ORM, admin, templates |
| `djangorestframework` | 3.17.1 | REST API — serializers, ViewSets, responses |
| `drf-spectacular` | 0.29.0 | Auto-generates OpenAPI schema → Swagger / ReDoc |
| `anthropic` | 0.88.0 | Claude API SDK — used only in `core/services/claude.py` |
| `pypdf` | 6.9.2 | PDF text extraction |
| `python-docx` | 1.2.0 | DOCX text extraction |
| `pytesseract` | 0.3.13 | PNG OCR (wraps the `tesseract` system binary) |
| `pillow` | 12.2.0 | Image handling — required by pytesseract |
| `python-dotenv` | 1.2.2 | Loads `.env` into `os.environ` at startup |

## Dev / test dependencies

| Package | Version | Purpose |
|---|---|---|
| `coverage` | 7.13.5 | Test coverage reporting |

## System dependency

`tesseract-ocr` must be installed on the host (or Docker image) for PNG extraction to work.

```bash
# macOS
brew install tesseract

# Debian / Ubuntu
apt-get install tesseract-ocr
```

If tesseract is not installed, PNG uploads will fail. All other file types (PDF, DOCX, TXT) work without it.

## Installing

```bash
venv/bin/pip install -r requirements.txt
```

## Notable choices

- **`pypdf` not `pypdf2`** — `pypdf2` is deprecated; `pypdf` is its maintained successor.
- **`python-dotenv` not `django-environ`** — lighter dependency, stdlib-compatible `.env` loading.
- **No `psycopg2`** — SQLite only for MVP. Add `psycopg2` when switching to PostgreSQL.
- **No task queue** — no Celery/Redis for MVP. Claude calls are synchronous.
