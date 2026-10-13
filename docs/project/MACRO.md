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

### User (UUID v7 as PK)
- `id` (UUID v7, PK, native PostgreSQL 18)
- `email` (VARCHAR(255), unique, not null)
- `password_hash` (VARCHAR(255), bcrypt, not null)
- `api_key` (VARCHAR(64), unique, auto-generated)
- `name` (VARCHAR(255))
- `email_verified` (BOOL, default false)
- `password_reset_token` (VARCHAR(255), nullable) ← for magic-link flow
- `password_reset_expires` (TIMESTAMP, nullable)
- `created_at` (TIMESTAMP, default now())
- `updated_at` (TIMESTAMP, default now())
- `is_active` (BOOL, default true)

### ShortUrl
- `id` (UUID v7, PK)
- `user_id` (UUID v7, FK → User.id)
- `original_url` (TEXT, not null)
- `short_code` (VARCHAR(16), unique, not null)
  - **Algorithm:** `base62(user_id[:5] + random_digits)`
  - Example: If user_id = `a1b2c3d4-e5f6...`, user_id[:5] = `a1b2c`
  - Random part: 6-10 random digits
  - Result: `a1b2c` + random → `a1b2c` + `3x4y5z` = `a1b2c3x4y5z`
- `click_count` (INT, default 0)
- `created_at` (TIMESTAMP, default now())
- `updated_at` (TIMESTAMP, default now())
- `expires_at` (TIMESTAMP, default now() + 1 month)
- `is_active` (BOOL, default true, soft delete)

### Analytics (Materialized View or Aggregated Table)
- `date` (DATE)
- `short_url_id` (UUID v7, FK)
- `user_id` (UUID v7, FK)
- `click_count` (INT)
- `created_at` (TIMESTAMP)

---

## API Surface

### Authentication (Phase 1.5)
| Endpoint | Method | Purpose | Auth | Notes |
|---|---|---|---|---|
| `POST /auth/signup` | POST | Register new user | None | Input: email, password, name |
| `POST /auth/login` | POST | Login (email + password) | None | Returns: api_key, user data |
| `POST /auth/password-reset-request` | POST | Request magic-link | None | Input: email; sends magic-link via email |
| `POST /auth/password-reset` | POST | Reset password with token | None | Input: reset_token, new_password |
| `POST /auth/verify-email` | POST | Verify email address | None | Input: verification_token (optional) |

### URL Shortening (Phase 2+)
| Endpoint | Method | Purpose | Auth | Notes |
|---|---|---|---|---|
| `POST /shorten` | POST | Create short URL | API Key / Bearer | Returns 201, short_code generated: user_id[:5] + random |
| `GET /{short_url}` | GET | Redirect to original | None (public) | Returns 302 Found, tracks click |
| `DELETE /shorten/{short_url}` | DELETE | Soft delete URL | API Key / Bearer | Returns 204 |
| `GET /shorten/{short_url}/metrics` | GET | View click analytics | API Key / Bearer | Returns daily click aggregates |

### Health & Documentation
| Endpoint | Method | Purpose | Auth | Notes |
|---|---|---|---|---|
| `GET /health` | GET | Health check (K8s liveness) | None | Returns 200 + status |
| `GET /docs` | GET | Swagger UI | None | Interactive API explorer |
| `GET /redoc` | GET | ReDoc | None | Static API documentation |

---

## Deployment Model

- **Local Dev:** docker-compose (PostgreSQL, Redis, app)
- **Production:** Docker image, PostgreSQL managed service, Redis managed service
- **Load Balancing:** Kubernetes or AWS ALB (external to this service)
- **CI/CD:** GitHub Actions (test, lint, build, push image)

---

## Security Considerations

1. **Password Hashing:** bcrypt (salted, slow hash, resistant to GPU attacks)
2. **API Key Auth:** Unique per user, stored as VARCHAR, validated per request
3. **Bearer Token (JWT):** Optional, for stateless auth (Phase 3)
4. **Email Verification:** Magic-link flow (email service out of scope)
5. **Password Reset:** Magic-link with TTL (15 min), invalidate after use
6. **Input Validation:** Pydantic + URL validation (OWASP)
7. **SQL Injection:** SQLC eliminates dynamic SQL
8. **Rate Limiting:** Per API key + per IP (Phase 3)
9. **CORS:** Configured in FastAPI
10. **Secrets Management:** .env, no hardcoded values, never log passwords/keys
11. **Account Lockout:** Optional, lock after N failed login attempts (Phase 3)

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
