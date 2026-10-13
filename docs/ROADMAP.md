# Roadmap — URL Shortener

## Timeline

| Phase | Duration | Focus | Status |
|---|---|---|---|
| **0** | Done ✅ | Setup (repo, venv, skeleton) | Complete |
| **1** | Week 1 | Foundation (User model, ShortUrl model, SQLC schema) | ⏳ TODO |
| **1.5** | ~2 days | User Management (signup, login, password reset, API key) | ⏳ TODO |
| **2** | Week 1-2 | Core API (POST /shorten, GET /{short_url} redirect 302) | ⏳ TODO |
| **3** | Week 2-3 | Advanced (custom URLs, expiry, click tracking, metrics) | ⏳ TODO |
| **4** | Week 3 | Caching (Redis integration, 80/20 Pareto) | ⏳ TODO |
| **5** | Week 4 | Infrastructure (Docker, OTEL, structured logging) | ⏳ TODO |
| **6** | Week 4 | Testing & Security (full suite, load testing, OWASP) | ⏳ TODO |

**Total Estimate:** 4-5 weeks (can be parallelized: phases 3-4, 5-6)  
**Team Size:** 1 (single developer, sequential flow recommended)

---

## Phase Dependencies

```
Phase 0 ✅
    ↓
Phase 1 (Foundation)
    └─ User model (UUID v7, email unique, password hash, api_key)
    └─ ShortUrl model (user_id FK, short_code = user_id[:5] + random)
    └─ Database schema + SQLC queries
    ↓
Phase 1.5 (User Management & Authentication)
    ├─ signup: email + password → create user, generate api_key
    ├─ login: email + password → return api_key
    ├─ password-reset-request: email → generate magic-link token
    └─ password-reset: token + new_password → update password
    ↓
Phase 2 (Core API)
    ├─ POST /shorten (requires API Key) → create short URL
    └─ GET /{short_url} (public) → 302 redirect + track click
    ↓
Phases 3-4 (can be parallel)
    ├─ Phase 3: Custom URLs + Expiry (1 month) + Click Tracking
    └─ Phase 4: Redis Cache (80/20 Pareto)
    ↓
Phases 5-6 (can be parallel)
    ├─ Phase 5: Docker + OTEL + Structured Logging
    └─ Phase 6: Full Test Suite (>80%) + Load Testing + OWASP
```

---

## Entry Points

### Start Phase 1
```bash
cd /home/mmb/pprojects/shortener-url
source venv/bin/activate
/spec "Phase 1: Define User model (UUID v7, email unique, password hash, api_key), ShortUrl model (user_id FK, short_code=user_id[:5]+random), database schema, and SQLC queries"
```

### Start Phase 1.5 (After Phase 1)
```bash
/spec "Phase 1.5: Implement user authentication (signup, login, password-reset with magic-link)"
```

### Run Locally (Any Phase)
```bash
docker-compose up -d
python -m uvicorn app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Run Tests
```bash
pytest --cov=app
```

---

## Success Criteria by Phase

**Phase 1:**
- [ ] User model with UUID v7 PK, email (unique), password_hash (bcrypt), api_key (unique)
- [ ] ShortUrl model with user_id FK, short_code unique
- [ ] Database schema (PostgreSQL 18 with UUID v7)
- [ ] SQLC queries generated (create user, read user, create shorturl, read shorturl, etc.)

**Phase 1.5:**
- [ ] POST /auth/signup → create user, return api_key
- [ ] POST /auth/login → validate email + password, return api_key
- [ ] POST /auth/password-reset-request → generate magic-link token
- [ ] POST /auth/password-reset → validate token, update password
- [ ] All endpoints tested, passwords hashed with bcrypt

**Phase 2:**
- [ ] POST /shorten (requires API Key) → short_code = base62(user_id[:5] + random), return 201
- [ ] GET /{short_url} → 302 redirect to original URL
- [ ] Click tracking working (increment click_count)
- [ ] All endpoints documented in Swagger

**Phase 3:**
- [ ] Custom URL support (max 16 chars, unique validation)
- [ ] URL expiry after 1 month (soft delete)
- [ ] Click tracking aggregation by day
- [ ] GET /shorten/{short_url}/metrics endpoint

**Phase 4:**
- [ ] Redis cache for URL lookups
- [ ] Cache invalidation on update/delete
- [ ] Cache hit rate > 80%, p99 latency < 100ms

**Phase 5:**
- [ ] Docker image builds (< 30s)
- [ ] docker-compose up -d = full stack
- [ ] OTEL instrumentation active
- [ ] Structured JSON logging

**Phase 6:**
- [ ] Code coverage > 80%
- [ ] Load test: 8000 req/s redirect throughput
- [ ] All OWASP Top 10 mitigations implemented
- [ ] Security audit passed

---

## Known Risks

1. **Concurrency:** Base62 collision handling (mitigated by unique constraint + retry)
2. **Performance:** 8000 req/s redirect throughput (mitigated by Redis 80/20 cache)
3. **Scaling:** Single Postgres instance (future: read replicas, connection pooling)
4. **Secret Management:** .env in Docker (future: secret service integration)

---

## Blockers (None Currently)

---

**Next:** Read `.prompts/SDLC-WORKFLOW.md` for prompt guide, then run `/spec` for Phase 1.
