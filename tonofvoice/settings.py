"""
Django settings for the Tone-of-Voice MVP project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tonofvoice.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tonofvoice.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "core" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Tone-of-Voice API",
    "VERSION": "0.1.0",
    "DESCRIPTION": """
Analyze brand documents and extract a structured **tone-of-voice signature**.
Use that signature to rewrite any text so it matches the brand's voice — powered by Claude AI.

---

## How it works

1. **Create a brand** — `POST /api/brands/`
2. **Upload documents** — `POST /api/brands/{id}/documents/` (PDF, DOCX, TXT, PNG)
3. **Extract signature** — `POST /api/brands/{id}/extract/` — Claude analyzes the documents and returns 5 tone-of-voice characteristics
4. **Transform text** — `POST /api/brands/{id}/transform/` — Claude rewrites your text in the brand's voice

---

## Signature characteristics

| Field | What it captures |
|---|---|
| `tone` | Emotional register and personality |
| `sentence_rhythm` | Sentence length, pacing, structural rules |
| `formality_level` | Conversational → institutional spectrum |
| `forms_of_address` | How the brand addresses the reader (you / we / one) |
| `emotional_appeal` | Rational vs. emotional persuasion mode |

---

## Errors

All errors return `{"error": "description"}`.
Status codes: `200 201 204 400 404 502`.
`502` means the Claude API failed — retry after a short delay.
""",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {
            "name": "brands",
            "description": (
                "Create and manage brands. Each brand holds a set of uploaded documents "
                "and a tone-of-voice signature extracted from them."
            ),
        },
        {
            "name": "documents",
            "description": (
                "Upload and manage brand documents. "
                "Accepted formats: PDF, DOCX, TXT, PNG (OCR). Max size: 20 MB. "
                "Text is extracted immediately at upload time and stored alongside the file."
            ),
        },
    ],
    "REDOC_SETTINGS": {
        "expandResponses": "200,201",
        "hideDownloadButton": False,
        "pathInMiddlePanel": True,
        "theme": {
            "colors": {
                "primary": {"main": "#2563eb"},
            },
            "typography": {
                "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                "fontSize": "15px",
                "lineHeight": "1.6",
                "headings": {
                    "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                    "fontWeight": "600",
                },
                "code": {
                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                    "fontSize": "13px",
                },
            },
            "sidebar": {
                "backgroundColor": "#0f172a",
                "textColor": "#cbd5e1",
                "width": "280px",
            },
            "rightPanel": {
                "backgroundColor": "#1e293b",
            },
        },
    },
}
