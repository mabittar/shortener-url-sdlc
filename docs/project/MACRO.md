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

## Observability Model (OTEL + LGTM Stack)

### Three Pillars of Observability

| Signal | Tool | Collection | Purpose |
|--------|------|-----------|---------|
| **Logs** | Loki | Structured JSON from FastAPI | Debugging, audit trail, event correlation |
| **Metrics** | Mimir | Prometheus scrape from `/metrics` | Performance tracking, SLO monitoring, alerting |
| **Traces** | Tempo | OTLP gRPC from OTEL SDK | Distributed tracing, latency analysis, bottleneck identification |

### LGTM Stack Ports & Access

| Service | Port | Access |
|---------|------|--------|
| **Grafana** (visualizations) | 3000 | http://localhost:3000 (admin/admin) |
| **Loki** (logs) | 3100 | http://localhost:3100 |
| **Tempo** (traces) | 3200 | http://localhost:3200 |
| **Mimir** (metrics) | 9009 | http://localhost:9009 |
| **OTEL Receiver** (gRPC) | 4317 | http://localhost:4317 |

### OpenTelemetry Instrumentation

**FastAPI:**
- All HTTP requests traced (method, path, status, duration)
- Request/response payload size
- User ID, API key (non-sensitive attributes)

**Database (SQLC):**
- SQL queries traced (operation, table, rows affected, duration)
- Connection pool utilization

**Redis:**
- Cache operations traced (get, set, delete, duration)
- Cache hit/miss rates

**Custom Business Metrics:**
- Counter: `short_urls.created` (per user, per day)
- Counter: `redirects.total` (per short_code, per day)
- Counter: `auth.login.attempts` (per email, success/failure)
- Gauge: `cache.hit_rate` (percentage)
- Histogram: `http.request.duration` (latency distribution)
- Histogram: `db.query.duration` (query latency)

### Grafana Dashboards (5 Total)

1. **Overview Dashboard**
   - Request rate (req/s)
   - Error rate (%)
   - P50, P95, P99 latency
   - Cache hit rate

2. **Authentication Dashboard**
   - Login success/failure rates
   - Rate limit locks per hour
   - Failed attempts by email
   - Signup rate

3. **URL Shortening Dashboard**
   - URLs created per hour
   - Redirect latency (p99)
   - Cache hit rate
   - Redirect throughput

4. **Infrastructure Dashboard**
   - Postgres connection pool utilization
   - Redis memory usage
   - Disk I/O
   - CPU usage

5. **Distributed Traces (Tempo)**
   - Trace search by service, operation, duration
   - Critical path analysis
   - Dependency graph: FastAPI → DB → Redis

### Structured JSON Logging

**Format:** Each log entry contains
- `timestamp` (ISO 8601)
- `level` (DEBUG, INFO, WARN, ERROR)
- `logger` (module/class name)
- `message` (human-readable)
- `trace_id` (for correlation with traces)
- `span_id` (for correlation with spans)
- `user_id` (if authenticated)
- `duration_ms` (request/operation duration)
- Context-specific fields (email, short_code, error_type, etc.)

**Example:**
```json
{
  "timestamp": "2026-10-12T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.controllers.auth",
  "message": "User login successful",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "user@example.com",
  "ip_address": "192.168.1.1",
  "duration_ms": 145,
  "trace_id": "abc123def456ghi789jkl012mno345pq",
  "span_id": "span789xyz"
}
```

### Alert Rules (via Mimir)

| Alert | Condition | Severity |
|-------|-----------|----------|
| **High Error Rate** | >5% errors over 5 min | Critical |
| **DB Connection Pool** | >90% utilization | Critical |
| **Redis Memory** | >80% used | Warning |
| **Slow Redirects** | p99 > 100ms | Warning |
| **Auth Rate Limit Spike** | >100 locks/hour | Warning |

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
