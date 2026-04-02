# API Endpoints

Base URL: `http://127.0.0.1:8000/api/`
All responses are JSON. No authentication required (MVP — localhost only).

Errors always return `{"error": "description"}`.
Status codes used: `200 201 204 400 404 502`.

Interactive docs: `GET /api/schema/swagger-ui/`

---

## Brands

### `GET /api/brands/`
List all brands.

### `POST /api/brands/`
Create a brand.
```json
{ "name": "Nuwacom", "description": "..." }
```
Returns `201`. `signature` is always `null` on creation.

### `GET /api/brands/{id}/`
Retrieve a brand. Returns `404` if not found.

### `PATCH /api/brands/{id}/`
Update `name` or `description`. `signature` is read-only — use `/extract/` to set it.

### `DELETE /api/brands/{id}/`
Delete brand and all its documents. Returns `204`.

**Brand object shape**
```json
{
  "id": 1,
  "name": "Nuwacom",
  "description": "B2B SaaS brand",
  "signature": {
    "tone": "authoritative yet approachable",
    "sentence_rhythm": "short declaratives followed by one elaborating clause",
    "formality_level": "semi-formal",
    "forms_of_address": "second person singular (you / your)",
    "emotional_appeal": "rational-first with aspirational payoff"
  },
  "created_at": "2025-04-01T10:00:00Z"
}
```

---

## Documents

### `GET /api/brands/{brand_id}/documents/`
List documents for a brand. Returns `404` if brand not found.

### `POST /api/brands/{brand_id}/documents/`
Upload a document. Send as `multipart/form-data` with a `file` field.

Accepted types: `pdf`, `docx`, `txt`, `png`. Max size: 20 MB.
Text is extracted immediately and stored. If extracted text exceeds 12,000 characters it is truncated (`"truncated": true`).

Returns `201` with the document object, or `400` on validation failure.

### `DELETE /api/brands/{brand_id}/documents/{id}/`
Delete a document. Returns `204`.

**Document object shape**
```json
{
  "id": 3,
  "brand": 1,
  "filename": "company_overview.pdf",
  "file_type": "pdf",
  "extracted_text": "At Nuwacom, we believe...",
  "truncated": false,
  "uploaded_at": "2025-04-01T10:05:00Z"
}
```

---

## Signature Extraction

### `POST /api/brands/{id}/extract/`
Analyze all uploaded documents with Claude and save the tone-of-voice signature. Overwrites any existing signature.

Request body: empty `{}`.

```json
{
  "brand_id": 1,
  "previous_signature_existed": false,
  "signature": {
    "tone": "...",
    "sentence_rhythm": "...",
    "formality_level": "...",
    "forms_of_address": "...",
    "emotional_appeal": "..."
  },
  "documents_analyzed": 3,
  "documents_truncated": 1
}
```

Errors: `400` if no documents exist, `502` on Claude API failure.

---

## Text Transformation

### `POST /api/brands/{id}/transform/`
Rewrite text in the brand's voice. Requires an existing signature.

Request body:
```json
{ "text": "Our software helps companies manage their communication better." }
```

Response:
```json
{
  "brand_id": 1,
  "original": "Our software helps companies manage their communication better.",
  "transformed": "Nuwacom gives your team the tools to communicate with precision.",
  "original_char_count": 62,
  "transformed_char_count": 63,
  "signature_used": { ... }
}
```

Errors: `400` if `text` is missing or brand has no signature, `502` on Claude failure.

---

## Schema / Docs

| URL | Description |
|---|---|
| `GET /api/schema/` | OpenAPI 3.0 schema |
| `GET /api/schema/swagger-ui/` | Swagger interactive UI |
| `GET /api/schema/redoc/` | ReDoc docs |
