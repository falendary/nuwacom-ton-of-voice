# Steps to Production

> Everything in this file is a **blocker or strong recommendation** before this application serves real users. Items are grouped by category, ordered roughly by dependency — infrastructure before application, application before observability.
>
> Each item links back to the relevant MVP limitation where applicable.

---

## 1 — Infrastructure & Deployment

### 1.1 Replace the development server with Gunicorn
The Django dev server (`manage.py runserver`) is single-threaded, not designed for concurrent load, and explicitly warns against production use.

```bash
pip install gunicorn
gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

- Configure worker count: `(2 × CPU cores) + 1` is the standard starting point
- Add `--timeout 120` to tolerate slow Claude API calls
- Run behind Nginx (or a load balancer) — Gunicorn should never be exposed directly to the internet

---

### 1.2 Dockerize the application
Every environment (dev, staging, prod) must run identical containers.

**Minimum Docker setup:**
```
Dockerfile          # app image
docker-compose.yml  # local dev: app + db + redis
docker-compose.prod.yml  # production overrides
.dockerignore
```

**Dockerfile requirements:**
- Multi-stage build — separate build and runtime stages to keep the image lean
- Non-root user — never run the container as root
- `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` env vars
- `tesseract-ocr` installed in the image (required for PNG extraction)
- Health check instruction

---

### 1.3 Switch to PostgreSQL
SQLite has no connection pooling and is not safe for concurrent writes. Replace before any real traffic.

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", default="5432"),
    }
}
```

- Add `psycopg2-binary` (dev) and `psycopg2` (prod) to requirements
- Add `django-db-geventpool` or `pgbouncer` for connection pooling under load
- Run migrations as a pre-deploy step, not at container startup

---

### 1.4 Deploy with a proper ingress / load balancer

**Recommended stack:**
- **Nginx** as reverse proxy in front of Gunicorn — handles SSL termination, static files, request buffering
- **Kubernetes Ingress** (nginx-ingress or Traefik) if deploying to K8s
- **AWS ALB / GCP Load Balancer** if deploying to a managed cloud

**Nginx config essentials:**
```nginx
upstream django {
    server app:8000;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    location /static/ { alias /app/staticfiles/; }
    location /media/  { alias /app/media/; }
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;   # tolerate Claude latency
    }
}
```

---

### 1.5 Object storage for uploaded files
`MEDIA_ROOT` on local disk disappears when containers restart. Replace with persistent object storage before going live.

- **AWS S3** → `django-storages[s3]`
- **GCS** → `django-storages[google]`
- **MinIO** (self-hosted S3-compatible) for on-premise deployments

Set `DEFAULT_FILE_STORAGE` in settings and add bucket lifecycle rules to auto-expire old uploads.

---

## 2 — Security

### 2.1 Django security settings hardening
Turn off every dev convenience before production:

```python
DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
SECRET_KEY = env("SECRET_KEY")  # long, random, rotated periodically

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

### 2.2 CSRF protection
Django's CSRF middleware is enabled by default — verify it is not disabled anywhere. For the REST API (consumed by a decoupled frontend), use DRF's session auth or token auth rather than disabling CSRF globally.

For cookie-based sessions: `CSRF_TRUSTED_ORIGINS` must list every frontend domain explicitly.

---

### 2.3 CORS
When the frontend lives on a different origin than the API:

```bash
pip install django-cors-headers
```

```python
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
# Never use CORS_ALLOW_ALL_ORIGINS = True in production
```

---

### 2.4 API authentication & authorization
The MVP has no API authentication. Production needs at minimum:

**Option A — JWT (stateless, recommended for SPA)**
```bash
pip install djangorestframework-simplejwt
```
- Access tokens (short-lived) + refresh tokens
- Rotate refresh tokens on use

**Option B — API key per brand/client**
- Suitable if the API is consumed by server-side integrations only
- Simpler to audit and revoke than JWT

**Option C — SSO via Keycloak (if org already runs Keycloak)**
- Use `mozilla-django-oidc` or `social-auth-app-django`
- Keycloak handles user provisioning, MFA, and group-based permissions
- Recommended if nuwacom has an existing identity provider — avoids maintaining a second user database

---

### 2.5 Role-based permissions
Once auth exists, protect every endpoint:

- `IsAuthenticated` as the global default in `DEFAULT_PERMISSION_CLASSES`
- Brand-level ownership — users should only read/write their own brands
- Admin-only endpoints for user management
- Consider multi-tenant isolation if multiple companies use the same deployment

---

### 2.6 API rate limiting
The transform endpoint calls Claude for every request — unbounded usage burns API budget fast.

```bash
pip install django-ratelimit
# or use DRF throttling:
```

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/hour",
        "user": "200/hour",
    },
}
```

Also set hard limits on the Anthropic API key (via Anthropic Console usage limits) as a second layer.

---

### 2.7 Secret management
No secrets in version control — ever. In production:

- **AWS Secrets Manager** or **HashiCorp Vault** for credentials at rest
- **Kubernetes Secrets** (encrypted at rest via etcd encryption) for K8s deployments
- Rotate `ANTHROPIC_API_KEY` and `SECRET_KEY` on a schedule
- Audit secret access logs

---

### 2.8 Input validation & file upload hardening
Uploaded files are a common attack vector:

- Validate MIME type server-side (not just extension) using `python-magic`
- Set a maximum file size limit (`FILE_UPLOAD_MAX_MEMORY_SIZE` in settings)
- Scan uploads with ClamAV or equivalent in high-security environments
- Never serve uploaded files from the same origin as the application — use a CDN or separate S3 presigned URLs

---

## 3 — Asynchronous Processing

### 3.1 Celery + Redis for background tasks
Claude signature extraction can take 5–15 seconds. Blocking the HTTP request thread is unacceptable in production.

```bash
pip install celery redis
```

- Move `extract_signature()` into a Celery task
- Return `202 Accepted` immediately with a `task_id`
- Add a `GET /api/tasks/{task_id}/` endpoint for status polling
- Or: use Django Channels + WebSockets to push progress updates

**Minimum Celery setup:**
```python
# celery.py
app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

Add a `celery` service to `docker-compose.yml`.

---

## 4 — Observability

### 4.1 Sentry for error tracking
Every unhandled exception in production should surface immediately.

```bash
pip install sentry-sdk[django]
```

```python
import sentry_sdk
sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    traces_sample_rate=0.1,   # 10% of transactions for performance monitoring
    send_default_pii=False,   # GDPR — don't send user data by default
)
```

- Set up Sentry alerts for new issue types and spike thresholds
- Use Sentry's performance monitoring to catch slow Claude calls
- Tag errors with `brand_id` for easier debugging

---

### 4.2 Structured logging
Replace Django's default logging with structured JSON logs — parseable by any log aggregation platform (Datadog, CloudWatch, Loki).

```bash
pip install structlog
```

Log at minimum: request method/path/status, brand_id on extraction/transform calls, Claude response time, truncation events, errors with stack traces.

---

### 4.3 Health check endpoints
Load balancers and K8s liveness/readiness probes need dedicated endpoints:

```
GET /health/live/   → 200 if the process is alive
GET /health/ready/  → 200 if DB connection + Anthropic reachability confirmed
```

```bash
pip install django-health-check
```

---

### 4.4 Metrics & alerting
Instrument the application with Prometheus metrics or Datadog APM:

- Request rate, error rate, latency (p50/p95/p99) per endpoint
- Claude API call duration histogram
- Active extraction tasks queue depth (if using Celery)
- Database connection pool utilization

Set alerts on: error rate spike, p99 latency > 30s, Claude API failures, disk usage on MEDIA_ROOT.

---

## 5 — CI/CD Pipeline

### 5.1 GitHub Actions (or equivalent)
Every push to `main` and every pull request should run:

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    steps:
      - name: Lint (ruff / flake8)
      - name: Type check (mypy)
      - name: Run tests (pytest / manage.py test)
      - name: Coverage gate (fail if <90%)
      - name: Security scan (bandit, safety)

  build:
    needs: test
    steps:
      - name: Build Docker image
      - name: Push to container registry
      - name: Deploy to staging (on merge to main)
```

- Never merge a PR that breaks tests or drops coverage below threshold
- Run `manage.py migrate --check` in CI to catch unapplied migrations before deploy

---

### 5.2 Separate staging environment
Production deploys should always pass through a staging environment first. Staging should:
- Mirror the production configuration exactly (same Docker image, same DB engine, same env vars except credentials)
- Run against a staging Anthropic API key with its own usage limits
- Be accessible to the team for manual QA before promoting

---

## 6 — Testing (beyond unit tests)

### 6.1 End-to-end tests
Unit tests mock Claude — E2E tests exercise the full stack against a real (or stubbed) Claude response.

```bash
pip install playwright  # or use Selenium / Cypress for the frontend
```

Minimum E2E scenarios:
- Upload a document → extract signature → verify signature fields populated
- Transform text → verify transformed text returned
- Upload unsupported file type → verify 400 response and user-facing error message

---

### 6.2 Load / performance tests
Before any significant traffic, verify the API holds under load.

```bash
pip install locust
# or: k6, Apache JMeter, Artillery
```

Minimum load test scenarios:
- 1,000 concurrent requests to `GET /api/brands/` (no Claude call — baseline)
- 50 concurrent requests to `POST /transform/` (Claude call — measure p95 latency and error rate)
- Ramp test: 0 → 200 users over 60 seconds — find the breaking point before production does

Target SLOs to define before go-live: p95 latency < 10s for transform, error rate < 0.1% at steady load.

---

### 6.3 Security / penetration testing
Before public exposure, run at minimum:

- OWASP ZAP automated scan against the API
- Manual review of file upload handling (path traversal, malicious content)
- Dependency audit: `pip-audit` or `safety check` on every release

---

## 7 — Frontend

### 7.1 Separate frontend repository
The Django templates UI is sufficient for MVP demo. For production:

- Create a dedicated repository (e.g. `nuwacom-tone-of-voice-frontend`)
- Framework choice: **React** (most widely adopted, large ecosystem) or **Vue 3** (gentler learning curve, good for smaller teams)
- Build with Vite; deploy as static assets to S3/CDN
- Communicate with the backend exclusively via the REST API
- Handle auth tokens, CSRF, and API error states properly in the client

---

### 7.2 SSO integration (Keycloak or existing provider)
If nuwacom runs an existing identity provider:

- **Keycloak** → `mozilla-django-oidc` on the backend; standard OIDC flow on the frontend
- **Auth0 / Okta** → similar OIDC setup
- **Google Workspace SSO** → `social-auth-app-django` with Google OAuth2 backend

Benefits: single user database, MFA enforcement, audit logs, no password management burden.

---

## 8 — Data & Compliance

### 8.1 GDPR / data privacy
Uploaded brand documents may contain personal data:

- Define a data retention policy — how long are documents stored after upload?
- Add a document deletion API and UI (MVP has delete, but no retention automation)
- Log what data is sent to the Anthropic API — Anthropic's data processing agreement may be required
- If serving EU users, review Anthropic's data residency options

### 8.2 Database backups
PostgreSQL in production needs automated backups:

- Daily full backups + continuous WAL archiving (point-in-time recovery)
- Test restore quarterly — a backup you've never restored is not a backup
- Store backups in a separate region from the application

---

## Summary Checklist

| Category | Item | Priority |
|---|---|---|
| Infra | Gunicorn production server | 🔴 Must |
| Infra | Docker + docker-compose | 🔴 Must |
| Infra | PostgreSQL | 🔴 Must |
| Infra | Nginx / ingress / load balancer | 🔴 Must |
| Infra | Object storage (S3 or equiv.) | 🔴 Must |
| Security | Django security settings hardened | 🔴 Must |
| Security | CSRF + CORS configured | 🔴 Must |
| Security | API authentication (JWT or SSO) | 🔴 Must |
| Security | Role-based permissions | 🔴 Must |
| Security | API rate limiting | 🔴 Must |
| Security | Secret management (no secrets in git) | 🔴 Must |
| Security | File upload hardening | 🟠 Should |
| Async | Celery + Redis for Claude calls | 🟠 Should |
| Observability | Sentry error tracking | 🔴 Must |
| Observability | Structured logging | 🟠 Should |
| Observability | Health check endpoints | 🔴 Must |
| Observability | Metrics + alerting | 🟠 Should |
| CI/CD | GitHub Actions: lint, test, coverage gate | 🔴 Must |
| CI/CD | Staging environment | 🟠 Should |
| Testing | End-to-end tests | 🟠 Should |
| Testing | Load tests (1,000+ req) | 🟠 Should |
| Testing | Security scan (OWASP ZAP, pip-audit) | 🟠 Should |
| Frontend | Separate frontend repository | 🟠 Should |
| Frontend | SSO / Keycloak integration | 🟡 Nice to have |
| Data | GDPR retention policy + deletion automation | 🟠 Should |
| Data | PostgreSQL automated backups | 🔴 Must |

**🔴 Must** — app should not go live without this
**🟠 Should** — high value, tackle in first production sprint
**🟡 Nice to have** — org-specific, schedule when relevant
