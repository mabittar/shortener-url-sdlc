# Claude.md — URL Shortener Project

**Project:** URL Shortener Service  
**Stack:** FastAPI, SQLC, PostgreSQL, Redis, Docker  
**Owner:** Marcel Bittar  
**Python:** 3.13  

---

## 🎯 Core Principles

### Architecture
- **Layered:** Model → Service → Controller → Infrastructure
- **Async-first:** FastAPI with async/await throughout
- **Type-safe:** Pydantic v2 for validation, SQLC for SQL generation, mypy strict
- **TDD:** Tests before implementation (pytest + asyncio)
- **Observable:** OTEL instrumentation, structured logging

### Code Quality
- **Linter:** Ruff (strict, all features)
- **Formatter:** Ruff format (100 char line-length)
- **Type Checking:** mypy strict mode
- **Coverage:** pytest-cov (target > 80%)
- **No Secrets:** .env ignored, use .env.example

### Validation & Errors
- **External input:** Validated with Pydantic at API boundary
- **Domain errors:** Custom exceptions, translated to HTTP responses
- **HTTP status codes:** Semantic (200 OK, 302 Found, 400 Bad Request, 409 Conflict, 500 Error)

---

## 📂 Project Structure

```
shortener-url/
├── .prompts/               ← Prompt templates (not git-tracked per se)
├── .github/
│   └── copilot_instructions.md
├── app/                    ← Main application package
│   ├── __init__.py
│   ├── main.py            ← FastAPI app entry point
│   ├── config.py          ← Configuration (pydantic_settings)
│   ├── models/            ← SQLAlchemy ORM or sqlc-generated models
│   ├── schemas/           ← Pydantic request/response schemas
│   ├── controllers/       ← API route handlers
│   ├── services/          ← Business logic
│   ├── infrastructure/    ← Database, cache, logging
│   └── exceptions.py      ← Domain-level exceptions
├── tests/                 ← Pytest suite
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── sql/                   ← sqlc SQL definitions
│   ├── schema/
│   └── queries/
├── pyproject.toml         ← Dependencies, tool config
├── sqlc.yaml              ← SQLc config
├── .env.example           ← Env var template
├── .gitignore
├── README.md
└── docker-compose.yml     ← Local dev stack (Postgres, Redis, nginx)
```

---

## 🔄 SDLC Workflow

**Method:** spec → plan → code → test → review (Henriquefy-integrated)

### Prompt Guide (Use These)

1. **Create Spec:** `.prompts/SDLC-PROMPT-SPEC.md`
   ```
   /spec "Feature: [name]"
   ```
   Output: `docs/specs/YYYYMMDD-FEATURE_spec.md`

2. **Create Plan:** `.prompts/SDLC-PROMPT-PLAN.md`
   ```
   /plan "Break down [spec-name]"
   ```
   Output: `tasks/plans/YYYYMMDD-FEATURE_plan.md`

3. **Implement:** `/code` executes tasks from plan

4. **Validate:** `/test` verifies acceptance criteria

5. **Review:** `/code-review` quality gate

---

## 📊 Phase Breakdown

### Phase 0: Setup ✅
- Git init, venv, dependencies, skeleton

### Phase 1: Foundation (Week 1)
**Spec:** Models, database schema, sqlc queries
```
/spec "Define User, ShortUrl models, database schema, sqlc queries"
```

### Phase 2: Core API (Week 1-2)
**Spec:** POST /shorten, GET /{short_url}
```
/spec "Implement POST /shorten endpoint with auto-generated base62 short code"
/spec "Implement GET /{short_url} endpoint with 302 redirect"
```

### Phase 3: Advanced Features (Week 2-3)
**Spec:** Custom URLs, expiry, click tracking
```
/spec "Add custom URL support with uniqueness validation (max 16 chars)"
/spec "Implement URL expiry after 1 month with soft delete"
/spec "Add click tracking and daily metrics aggregation"
```

### Phase 4: Caching & Optimization (Week 3)
**Spec:** Redis integration, connection pooling
```
/spec "Implement Redis cache for URL lookups (80/20 Pareto rule)"
```

### Phase 5: Infrastructure & Observability (Week 4)
**Spec:** Docker, Nginx, OTEL, structured logging
```
/spec "Setup Docker + docker-compose for PostgreSQL + Redis + Nginx"
/spec "Add OTEL instrumentation and structured JSON logging"
```

### Phase 6: Testing & Security (Week 4)
**Spec:** Full test suite, load testing, OWASP mitigations
```
/spec "Write unit + integration + E2E tests with > 80% coverage"
/spec "Implement load testing for 8000 concurrent redirects/second"
```

---

## 🧪 Testing Convention

**Test-first:**
1. Write test (test file in `tests/unit/`, `tests/integration/`, or `tests/e2e/`)
2. Run pytest (fails)
3. Implement feature
4. Run pytest (passes)
5. Refactor if needed

**Test structure:**
```python
# tests/unit/test_short_url_service.py
import pytest
from app.services.short_url_service import generate_short_code

def test_generate_short_code_is_unique():
    code1 = generate_short_code("https://example.com/long")
    code2 = generate_short_code("https://example.com/other")
    assert code1 != code2
```

---

## 📝 Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, refactor, test, docs, chore, perf  
**Scope:** (optional) model, service, controller, infra  
**Subject:** Imperative, present tense, no period

Example:
```
feat(controller): add POST /shorten endpoint

- Accept long_url and optional custom_url
- Validate input with Pydantic
- Call service to generate short code
- Return 201 with Location header

Closes #1
```

---

## 🚀 Development Workflow

### Startup
```bash
cd shortener-url
source venv/bin/activate
cp .env.example .env  # Edit with local DB credentials
docker-compose up -d  # Start PostgreSQL + Redis
python -m uvicorn app.main:app --reload
```

### Testing
```bash
pytest                                    # All tests
pytest tests/unit/ -v                     # Unit only
pytest --cov=app --cov-report=html       # Coverage report
```

### Code Quality
```bash
ruff check app/ tests/                    # Lint
ruff format app/ tests/                   # Format
mypy app/                                 # Type check
```

### Database
```bash
# After schema changes, regenerate sqlc
sqlc generate
```

---

## 🔐 Secrets & Config

- **Never commit .env** (in .gitignore)
- Use `.env.example` for template
- Load with `pydantic_settings` in `config.py`
- In Docker, pass via environment or secrets file

---

## 📞 Quick Ref: Key Files to Edit First

| Phase | Files |
|-------|-------|
| 1 | `app/models/`, `sql/schema/`, `app/config.py` |
| 2 | `app/controllers/`, `app/schemas/` |
| 3 | `app/services/`, tests |
| 4 | `app/infrastructure/cache.py` |
| 5 | `docker-compose.yml`, `app/observability.py` |
| 6 | `tests/`, `pyproject.toml` (mypy/ruff config) |

---

## 🎓 References

- **SDLC:** 6 phases, TDD-first, async throughout
- **Database:** PostgreSQL + sqlc for type safety
- **Cache:** Redis with 80/20 rule (Pareto)
- **API:** FastAPI with 302 redirects for analytics
- **Observability:** OTEL + structured logging
- **Quality:** Ruff + mypy strict + pytest > 80% coverage

---

*Last updated: 2026-10-12*
