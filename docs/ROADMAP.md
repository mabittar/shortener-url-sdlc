# Roadmap — URL Shortener

## Timeline

| Phase | Duration | Focus | Status |
|---|---|---|---|
| **0** | Done ✅ | Setup (repo, venv, skeleton) | Complete |
| **1** | Week 1 | Foundation (models, schema, sqlc) | ⏳ TODO |
| **2** | Week 1-2 | Core API (create, redirect) | ⏳ TODO |
| **3** | Week 2-3 | Advanced (custom URLs, expiry, analytics) | ⏳ TODO |
| **4** | Week 3 | Caching (Redis integration) | ⏳ TODO |
| **5** | Week 4 | Infrastructure (Docker, OTEL, logging) | ⏳ TODO |
| **6** | Week 4 | Testing & Security (full suite, load testing) | ⏳ TODO |

**Total Estimate:** 4-5 weeks  
**Team Size:** 1 (parallel work possible in phases 3-6)

---

## Phase Dependencies

```
Phase 0 ✅ (Setup complete)
    ↓
Phase 1 (Foundation: Models + Schema + SQLC)
    ↓
Phase 2 (Core API: POST /shorten + GET /{short_url} with 302 redirect)
    ↓
Phases 3-4 (parallel: Features + Caching)
    ├─ Phase 3: Custom URLs + Expiry + Click Tracking
    └─ Phase 4: Redis Cache (80/20 Pareto)
    ↓
Phases 5-6 (parallel: Infrastructure + Testing)
    ├─ Phase 5: Docker + OTEL + Structured Logging
    └─ Phase 6: Full Test Suite + Load Testing + OWASP
```

---

## Entry Points

### Start Phase 1
```bash
cd /home/mmb/pprojects/shortener-url
source venv/bin/activate
/spec "Define User model, ShortUrl model, database schema, and sqlc queries"
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

**Phase 1:** Models + schema + sqlc queries ready  
**Phase 2:** POST /shorten + GET /{short_url} working  
**Phase 3:** Custom URLs + expiry + click tracking  
**Phase 4:** Redis cache integrated, cache hits working  
**Phase 5:** Docker image builds, OTEL active  
**Phase 6:** Coverage > 80%, load test passes, security audit passes

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
