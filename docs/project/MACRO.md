# Macro Definition — URL Shortener

**Project:** URL Shortener Service  
**Owner:** Marcel Bittar  
**Created:** 2026-10-12  
**Status:** Approved  

---

## Business Goals

1. **REST API Service** for third-party clients to shorten URLs
2. **Fast redirects** (302, not 301) with click tracking for analytics
3. **Custom aliases** support (max 16 chars) with uniqueness validation
4. **High availability & performance** — 8000 req/s, p99 < 100ms
5. **Observability** — OTEL tracing, structured logging, metrics

---

## Stack Decisions

| Component | Choice | Rationale |
|---|---|---|
| **Framework** | FastAPI | Async, modern, type-safe, great for APIs |
| **Database** | PostgreSQL | ACID, mature, handles concurrent writes |
| **SQL Generation** | SQLC | Type-safe, no ORM overhead, explicit queries |
| **Async Driver** | Psycopg 3 | Non-blocking, modern, PostgreSQL-native |
| **Caching** | Redis | In-memory, 80/20 rule applicable, simple |
| **Validation** | Pydantic v2 | Fast, strict, good error messages |
| **Testing** | pytest + asyncio | Standard, good async support |
| **Linting** | Ruff | Fast, comprehensive, Python 3.13 support |
| **Containerization** | Docker + Compose | Local dev parity with production |
| **Observability** | OTEL + structured logs | Standard, vendor-neutral |

---

## Architectural Principles

1. **Layered Architecture**
   - Controllers (API routes)
   - Services (business logic)
   - Repositories (data access)
   - Infrastructure (DB, cache)

2. **Type Safety**
   - Pydantic for I/O validation
   - SQLC for SQL generation
   - mypy strict mode

3. **TDD-First**
   - Tests before implementation
   - > 80% coverage target
   - Unit + Integration + E2E

4. **Async Throughout**
   - No blocking I/O
   - Psycopg 3 async, Redis async
   - FastAPI async routes

5. **Observable by Default**
   - OTEL instrumentation
   - Structured JSON logging
   - Prometheus metrics

---

## Non-Functional Requirements

| Requirement | Target | Rationale |
|---|---|---|
| **Read/Write Ratio** | 200:1 | Redirects >> creates |
| **Throughput** | 8000 req/s reads | 40 URLs/sec writes |
| **Latency (p99)** | < 100ms | SLO for redirects |
| **Availability** | 99.9% | High uptime |
| **Cache Hit Rate** | 80% | Pareto rule on hot URLs |
| **TTL (Expiry)** | 1 month | Business requirement |

---

## Data Model

### User
- `id` (UUID)
- `api_key` (unique string, hashed)
- `name`
- `created_at`

### ShortUrl
- `id` (UUID)
- `user_id` (FK)
- `original_url` (TEXT)
- `short_code` (VARCHAR(16), unique)
- `click_count` (INT)
- `created_at`
- `updated_at`
- `expires_at` (nullable, default +1 month)
- `is_active` (BOOL, soft delete)

### Analytics (optional materialized view)
- `date` (DATE)
- `short_url_id` (FK)
- `click_count` (INT)

---

## API Surface

| Endpoint | Method | Purpose | Auth | Notes |
|---|---|---|---|---|
| `POST /shorten` | POST | Create short URL | API Key | Returns 201, Location header |
| `GET /{short_url}` | GET | Redirect to original | None (public) | Returns 302 Found, no 301 |
| `DELETE /shorten/{short_url}` | DELETE | Soft delete URL | API Key | Returns 204 |
| `GET /shorten/{short_url}/metrics` | GET | View click analytics | API Key | Returns daily aggregates |
| `GET /health` | GET | Health check | None | Returns 200 + status |
| `GET /docs` | GET | Swagger UI | None | Interactive API docs |
| `GET /redoc` | GET | ReDoc | None | Alternative API docs |

---

## Deployment Model

- **Local Dev:** docker-compose (PostgreSQL, Redis, app)
- **Production:** Docker image, PostgreSQL managed service, Redis managed service
- **Load Balancing:** Kubernetes or AWS ALB (external to this service)
- **CI/CD:** GitHub Actions (test, lint, build, push image)

---

## Security Considerations

1. **Input Validation:** Pydantic + URL validation (OWASP)
2. **API Key Auth:** Simple header validation or JWT (Phase 3)
3. **SQL Injection:** SQLC eliminates dynamic SQL
4. **Rate Limiting:** Per API key (Phase 3)
5. **CORS:** Configured in FastAPI
6. **Secrets Management:** .env, no hardcoded values

---

## Observability Model

| Signal | Tool | Purpose |
|---|---|---|
| Logs | Structured JSON (uvicorn + custom) | Debugging, audit |
| Metrics | Prometheus (FastAPI middleware) | Performance, SLO tracking |
| Traces | OTEL (FastAPI, database, cache) | Latency analysis, bottleneck identification |

---

## Success Metrics

- [ ] All endpoints tested (unit + integration + E2E)
- [ ] Code coverage > 80%
- [ ] Linting passes (Ruff, mypy strict)
- [ ] Latency p99 < 100ms
- [ ] Handles 8000 req/s under load
- [ ] Docker build < 30s
- [ ] Deployment < 5 min

---

**Signed off:** 2026-10-12  
**Next:** Run `/spec` for Phase 1 Foundation
