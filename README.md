# Tone-of-Voice MVP

A Django application that extracts a brand's tone-of-voice signature from uploaded documents using Claude (Anthropic), then applies that signature to rewrite arbitrary text — keeping the message, shifting the voice.

---

## Prerequisites

- Python 3.11+
- `pip`
- An Anthropic API key → [console.anthropic.com](https://console.anthropic.com)
- `tesseract-ocr` installed on your system (for PNG uploads)
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt install tesseract-ocr`

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/falendary/nuwacom-ton-of-voice.git
cd nuwacom-ton-of-voice

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Apply migrations
python manage.py migrate

# 6. Create a superuser (for Django Admin access)
python manage.py createsuperuser

# 7. (Optional) Load demo data
python manage.py loaddata demo_data/fixture.json
```

---

## Running Locally

```bash
python manage.py runserver
```

The app is now available at **http://127.0.0.1:8000**

---

## Accessing the App

| URL | What it is |
|---|---|
| `http://127.0.0.1:8000/` | Main UI — upload documents, transform text |
| `http://127.0.0.1:8000/admin/` | Django Admin — manage brands, documents, signatures |
| `http://127.0.0.1:8000/api/` | REST API root |
| `http://127.0.0.1:8000/api/schema/swagger-ui/` | Swagger UI |
| `http://127.0.0.1:8000/api/schema/redoc/` | ReDoc |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `SECRET_KEY` | ✅ | Django secret key (auto-generated in `.env.example`) |
| `DEBUG` | — | Defaults to `True` for local dev |
| `ALLOWED_HOSTS` | — | Defaults to `*` for local dev |

---

## Running Tests

```bash
python manage.py test
```

With coverage report:

```bash
pip install coverage
coverage run manage.py test
coverage report -m
```

---

## Project Structure

```
nuwacom-ton-of-voice/
├── core/                  # Main Django app
│   ├── models.py          # Brand, Document, Signature
│   ├── views.py           # Template views
│   ├── serializers.py     # DRF serializers
│   ├── api_views.py       # REST API views
│   ├── services/
│   │   └── claude.py      # Claude API integration
│   ├── tests/
│   │   ├── test_models.py
│   │   ├── test_api.py
│   │   └── test_services.py
│   └── templates/
│       ├── upload.html
│       └── transform.html
├── demo_data/             # Sample brand documents
│   ├── nuwacom/
│   └── apple/
├── manage.py
├── requirements.txt
├── .env.example
├── PLAN.md
├── ENDPOINTS.md
└── README.md
```

---

## Known Limitations

See [`PLAN.md`](./PLAN.md#intended-limitations) for the full list. In short: localhost only, no production security, synchronous Claude calls, SQLite.
