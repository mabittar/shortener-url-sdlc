# Copilot Instructions — URL Shortener

**Project:** URL Shortener Service  
**Stack:** FastAPI, SQLC, PostgreSQL, Redis  
**Code Style:** Ruff (100 char line-length), mypy strict, TDD-first  

---

## Command Reference

### Setup
```bash
source venv/bin/activate
docker-compose up -d
python -m uvicorn app.main:app --reload
```

### Quality
```bash
ruff check app/ tests/     # Lint
ruff format app/ tests/    # Format
mypy app/                  # Type check
pytest                     # Tests
```

### Database
```bash
sqlc generate              # Regenerate from SQL
```

---

## Quick Rules

1. **Test first:** Write test → implement → pass
2. **Pydantic for I/O:** All external input validated
3. **Type annotations:** Strict mypy required
4. **No secrets in git:** .env in .gitignore, use .env.example
5. **Exceptions:** Custom domain errors, translate to HTTP at boundary
6. **Async:** Use async/await, not threading
7. **Ruff format:** Run before commit

---

## File Templates

### New Controller
```python
# app/controllers/example.py
from fastapi import APIRouter, HTTPException, status
from app.schemas import ExampleRequest, ExampleResponse
from app.services import example_service

router = APIRouter(prefix="/example", tags=["example"])

@router.post("/", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(req: ExampleRequest) -> ExampleResponse:
    """Create an example."""
    try:
        result = await example_service.create(req)
        return ExampleResponse.model_validate(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### New Service
```python
# app/services/example_service.py
from app.models import Example
from app.infrastructure.db import get_db

async def create(req) -> Example:
    """Business logic for creating example."""
    # Validation, business rules
    async with get_db() as db:
        # sqlc generated query
        return await db.create_example(...)
```

### New Test
```python
# tests/unit/test_example_service.py
import pytest
from app.services import example_service

@pytest.mark.asyncio
async def test_create_example():
    result = await example_service.create(...)
    assert result.id is not None
```

---

## API Conventions

- **POST /shorten** → Create short URL, return 201 with Location
- **GET /{short_url}** → Redirect (302), not 301
- **POST /shorten/{id}/deactivate** → Soft delete
- **GET /metrics** → Analytics (requires auth)

---

## Packages

- `FastAPI`, `uvicorn` — Web framework
- `SQLAlchemy` + `Psycopg3` — Database (async)
- `sqlc` — Type-safe SQL code gen
- `Pydantic v2` — Validation
- `Redis` — Cache
- `pytest`, `pytest-asyncio` — Testing
- `Ruff` — Linting/formatting
- `mypy` — Type checking

---

## Endpoints Checklist

- [ ] `POST /shorten` — Create short URL
- [ ] `GET /{short_url}` — Redirect to original
- [ ] `POST /{short_url}/deactivate` — Soft delete
- [ ] `GET /metrics?days=7` — Analytics (optionally auth)
- [ ] `GET /health` — Health check
- [ ] `POST /auth` — API key validation (optional)

---

*Keep it simple. Keep it fast. Keep it tested.*
