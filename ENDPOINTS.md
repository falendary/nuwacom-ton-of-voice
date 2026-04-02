# API Endpoints Reference

Base URL: `http://127.0.0.1:8000/api/`

All requests and responses use `application/json` unless noted.
Authentication: none required for MVP (localhost only).

---

## Error Envelope

All errors follow this consistent shape:

```json
{
  "error": "Human-readable description of what went wrong"
}
```

HTTP status codes used: `200`, `201`, `204`, `400`, `404`, `502`.

---

## Brands

### `GET /api/brands/`
List all brands.

**Response `200`**
```json
[
  {
    "id": 1,
    "name": "Nuwacom",
    "description": "B2B SaaS brand — clarity-first, empowering tone",
    "signature": {
      "tone": "authoritative yet approachable — leads with clarity, never with urgency",
      "sentence_rhythm": "short declaratives followed by one elaborating clause; avoids run-ons",
      "formality_level": "semi-formal — professional enough for B2B, human enough to avoid stiffness",
      "forms_of_address": "second person singular (you / your); occasional we-inclusive",
      "emotional_appeal": "rational-first with aspirational payoff; benefits before feelings"
    },
    "created_at": "2025-04-01T10:00:00Z"
  }
]
```

---

### `POST /api/brands/`
Create a new brand.

**Request body**
```json
{
  "name": "Nuwacom",
  "description": "B2B SaaS brand — clarity-first, empowering tone"
}
```

**Response `201`**
```json
{
  "id": 1,
  "name": "Nuwacom",
  "description": "B2B SaaS brand — clarity-first, empowering tone",
  "signature": null,
  "created_at": "2025-04-01T10:00:00Z"
}
```

---

### `GET /api/brands/{id}/`
Retrieve a single brand with its current signature.

**Response `200`** — same shape as list item above.

**Error `404`**
```json
{ "error": "Brand not found." }
```

---

### `PATCH /api/brands/{id}/`
Partial update — name or description only. Does not touch the signature.

**Request body**
```json
{
  "description": "Updated description"
}
```

**Response `200`** — full brand object.

---

### `DELETE /api/brands/{id}/`
Delete a brand and all its associated documents.

**Response `204`** — no body.

---

## Documents

### `GET /api/brands/{brand_id}/documents/`
List all documents uploaded for a brand.

**Response `200`**
```json
[
  {
    "id": 3,
    "brand": 1,
    "filename": "company_overview.pdf",
    "file_type": "pdf",
    "extracted_text": "At Nuwacom, we believe that every team...",
    "truncated": false,
    "uploaded_at": "2025-04-01T10:05:00Z"
  }
]
```

`truncated: true` means the extracted text exceeded 12,000 characters and was cut before storage.

---

### `POST /api/brands/{brand_id}/documents/`
Upload a new document. Send as `multipart/form-data`.

**Request** (`multipart/form-data`)
```
file: <binary>    # required — PDF, DOCX, TXT, or PNG
```

**Response `201`**
```json
{
  "id": 3,
  "brand": 1,
  "filename": "company_overview.pdf",
  "file_type": "pdf",
  "extracted_text": "At Nuwacom, we believe that every team...",
  "truncated": false,
  "uploaded_at": "2025-04-01T10:05:00Z"
}
```

**Error `400`** — unsupported file type
```json
{
  "error": "Unsupported file type. Accepted: pdf, docx, txt, png"
}
```

**Error `400`** — empty or unreadable file
```json
{
  "error": "Could not extract text from the uploaded file."
}
```

---

### `DELETE /api/brands/{brand_id}/documents/{id}/`
Remove a document. Does not trigger re-extraction automatically.

**Response `204`** — no body.

---

## Signature Extraction

### `POST /api/brands/{brand_id}/extract/`
Trigger Claude to analyze all uploaded documents for this brand and derive the tone-of-voice signature. Overwrites any existing signature.

**Request body** — empty `{}`

**Response `200`**
```json
{
  "brand_id": 1,
  "previous_signature_existed": false,
  "signature": {
    "tone": "authoritative yet approachable — leads with clarity, never with urgency",
    "sentence_rhythm": "short declaratives followed by one elaborating clause; avoids run-ons",
    "formality_level": "semi-formal — professional enough for B2B, human enough to avoid stiffness",
    "forms_of_address": "second person singular (you / your); occasional we-inclusive",
    "emotional_appeal": "rational-first with aspirational payoff; benefits before feelings"
  },
  "documents_analyzed": 3,
  "documents_truncated": 1
}
```

`previous_signature_existed` — `true` if a signature already existed and was overwritten.
`documents_truncated` — count of documents whose text was capped at 12,000 chars.

**Error `400`** — no documents uploaded yet
```json
{
  "error": "No documents found for this brand. Upload at least one document before extracting."
}
```

**Error `502`** — Claude API failure
```json
{
  "error": "Claude API error: <upstream message>"
}
```

---

## Text Transformation

### `POST /api/brands/{brand_id}/transform/`
Rewrite user-supplied text in the brand's tone-of-voice. Requires an existing signature.

**Request body**
```json
{
  "text": "Our software helps companies manage their communication better and saves time."
}
```

**Response `200`**
```json
{
  "brand_id": 1,
  "original": "Our software helps companies manage their communication better and saves time.",
  "transformed": "Nuwacom gives your team the tools to communicate with precision — freeing up hours you didn't know you were losing.",
  "original_char_count": 78,
  "transformed_char_count": 111,
  "signature_used": {
    "tone": "authoritative yet approachable — leads with clarity, never with urgency",
    "sentence_rhythm": "short declaratives followed by one elaborating clause; avoids run-ons",
    "formality_level": "semi-formal — professional enough for B2B, human enough to avoid stiffness",
    "forms_of_address": "second person singular (you / your); occasional we-inclusive",
    "emotional_appeal": "rational-first with aspirational payoff; benefits before feelings"
  }
}
```

**Error `400`** — missing text field
```json
{
  "error": "Field 'text' is required."
}
```

**Error `400`** — no signature extracted yet
```json
{
  "error": "No signature found for this brand. Run POST /extract/ first."
}
```

**Error `502`** — Claude API failure
```json
{
  "error": "Claude API error: <upstream message>"
}
```

---

## API Schema

| URL | Description |
|---|---|
| `GET /api/schema/` | OpenAPI 3.0 schema (JSON or YAML via `?format=yaml`) |
| `GET /api/schema/swagger-ui/` | Swagger interactive docs |
| `GET /api/schema/redoc/` | ReDoc clean docs |
