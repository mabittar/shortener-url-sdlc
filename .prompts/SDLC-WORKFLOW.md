# SDLC Workflow — URL Shortener

## Standard Flow

```
1. SPEC   → Understand what to build
   /spec "[feature description]"
   
2. PLAN   → Break into sequential tasks
   /plan "[based on approved spec]"
   
3. CODE   → Implement each task
   /code "[task-specific implementation]"
   
4. TEST   → Verify acceptance criteria
   /test "[feature/scenario]"
   
5. REVIEW → Quality gate
   /code-review [pr-or-branch]
```

---

## Phase Breakdown for This Project

### Phase 1: Foundation (Week 1)
**Input:** input.txt requirements + system design goals
**Output:** Spec for models, database schema, sqlc queries

**Spec:**
```
/spec "Define User model, ShortUrl model, database schema, and sqlc queries"
```

**Plan:**
```
/plan "Create tasks for database models and migrations"
```

---

### Phase 2: Core API (Week 1-2)
**Input:** Phase 1 models + Foundation spec
**Output:** POST /shorten, GET /{short_url} endpoints

**Spec:**
```
/spec "Implement POST /shorten endpoint with auto-generated base62 short code"
/spec "Implement GET /{short_url} endpoint with 302 redirect"
```

**Plan:**
```
/plan "Break down API endpoints into controller/service/repository tasks"
```

---

### Phase 3: Advanced Features (Week 2-3)
**Input:** Phase 2 APIs + Functional requirements
**Output:** Custom URLs, expiry, metrics

**Spec:**
```
/spec "Add custom URL support with uniqueness validation (max 16 chars)"
/spec "Implement URL expiry after 1 month with soft delete"
/spec "Add click tracking and daily metrics aggregation"
```

**Plan:**
```
/plan "Create tasks for custom URL feature"
/plan "Create tasks for expiry and metrics"
```

---

### Phase 4: Caching & Optimization (Week 3)
**Input:** Phase 3 completed + Performance requirements
**Output:** Redis integration, connection pooling

**Spec:**
```
/spec "Implement Redis cache for URL lookups (80/20 Pareto rule)"
```

**Plan:**
```
/plan "Create tasks for Redis integration and cache invalidation"
```

---

### Phase 5: Infrastructure & Observability (Week 4)
**Input:** Phases 1-4 + Non-functional requirements
**Output:** Docker, Nginx, OTEL, logging

**Spec:**
```
/spec "Setup Docker image and docker-compose for PostgreSQL + Redis + Nginx"
/spec "Add OTEL instrumentation for FastAPI, database, cache"
/spec "Implement structured JSON logging and Prometheus metrics"
```

**Plan:**
```
/plan "Create tasks for Docker and OTEL setup"
```

---

### Phase 6: Testing & Security (Week 4)
**Input:** All phases completed
**Output:** Full test suite, load testing, security hardening

**Spec:**
```
/spec "Write unit + integration + E2E tests with > 80% coverage"
/spec "Add load testing for 8000 concurrent redirects/second"
/spec "Implement input validation and OWASP Top 10 mitigations"
```

**Plan:**
```
/plan "Create tasks for test suite completion"
```

---

## When to Use Each Skill

| Skill | Trigger | Output |
|---|---|---|
| `/spec` | New feature, unclear requirements, design validation | Markdown spec with acceptance criteria |
| `/plan` | Spec approved, ready to sequence | Task breakdown with commit order |
| `/code` | Plan approved, ready to implement | Implementation in code |
| `/test` | Code done, feature ready for validation | Tests + coverage report |
| `/code-review` | PR ready, quality gate | Review findings + approval |

---

## Commit Message Template

Use this after each task completes:

```
feat(scope): [TASK-XX] Brief description

- First point
- Second point

Closes [issue-number] or References [spec/plan]
```

Example:
```
feat(api): [TASK-01] Implement POST /shorten endpoint

- Accept long_url and optional custom_url
- Validate input with Pydantic
- Generate base62 short code or validate custom URL
- Store in database via sqlc
- Return 201 with Location header

References docs/specs/20261012-CORE-API_spec.md
```

---

## Quick Reference

**Need a spec?** Start with `/spec "[feature name]"`  
**Spec approved?** Run `/plan` to break it down  
**Plan approved?** Run `/code` to implement  
**Code done?** Run `/test` to validate  
**Before merge?** Run `/code-review` for quality check  

**Local dev?** `source venv/bin/activate && python -m uvicorn app.main:app --reload`  
**Run tests?** `pytest --cov=app`  
**Lint/format?** `ruff check app/ && ruff format app/`  
