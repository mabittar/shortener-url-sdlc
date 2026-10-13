# Quick Setup — URL Shortener

## Prerequisites

- Python 3.13
- Docker & Docker Compose
- VS Code (optional, configs provided)

---

## Local Development

### 1. Clone & Activate
```bash
cd /home/mmb/pprojects/shortener-url
source venv/bin/activate
```

### 2. Copy Environment
```bash
cp .env.example .env
# Edit .env if needed (defaults work with docker-compose)
```

### 3. Start Services
```bash
docker-compose up -d
# Waits for Postgres + Redis to be healthy
```

### 4. Run App
```bash
# Option A: VS Code (F5, select "FastAPI")
# Option B: Terminal
python -m uvicorn app.main:app --reload
```

**API:** http://localhost:8000  
**Docs:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc  

---

## Code Quality

### Format
```bash
ruff format app/ tests/
```

### Lint
```bash
ruff check app/ tests/
```

### Type Check
```bash
mypy app/
```

### All at Once
```bash
ruff format app/ tests/ && ruff check app/ tests/ && mypy app/
```

---

## Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

### Run Single Test
```bash
pytest tests/unit/test_example.py::test_example -v
```

### Debug a Test
```bash
pytest tests/unit/test_example.py -v -s  # Show prints
```

---

## Database

### Regenerate SQLC (after schema changes)
```bash
sqlc generate
```

### Postgres Shell
```bash
docker exec -it shortener-db psql -U shortener_user -d shortener_url
```

### Reset Database
```bash
docker-compose down -v
docker-compose up -d
```

---

## SDLC Workflow

### Start New Phase
1. Read `.prompts/SDLC-WORKFLOW.md`
2. Run `/spec "[feature description]"`
3. Wait for spec approval
4. Run `/plan "[spec-name]"`
5. Execute tasks from plan with `/code`

### Example (Phase 1)
```
/spec "Define User model, ShortUrl model, database schema, and sqlc queries"
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Docker Issues
```bash
# Clean restart
docker-compose down -v
docker-compose up -d
```

### Module Not Found
```bash
# Reinstall in dev mode
pip install -e ".[dev]"
```

### Database Connection Error
```bash
# Check Postgres is healthy
docker-compose logs postgres
docker-compose exec postgres pg_isready -U shortener_user
```

---

## Project Structure

```
shortener-url/
├── app/                    # Main application
│   ├── main.py            # FastAPI app
│   ├── config.py          # Configuration
│   ├── models/            # ORM/SQLAlchemy (Phase 1)
│   ├── schemas/           # Pydantic (Phase 1)
│   ├── controllers/       # Routes (Phase 2)
│   ├── services/          # Logic (Phase 2+)
│   └── infrastructure/    # DB, cache, logging (Phase 4+)
├── tests/                 # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── sql/                   # SQLC definitions
│   ├── schema/
│   └── queries/
├── docs/                  # Documentation
│   ├── project/MACRO.md   # Architecture decisions
│   └── specs/            # Phase specs (generated)
├── .prompts/             # Prompt templates
├── .vscode/              # VS Code config
├── Claude.md             # This project's rules
├── .github/
│   └── copilot_instructions.md  # Short ref
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml        # Dependencies + tools
```

---

## Next Steps

1. **Read architecture:** `docs/project/MACRO.md`
2. **Read roadmap:** `docs/ROADMAP.md`
3. **Read workflow:** `.prompts/SDLC-WORKFLOW.md`
4. **Run Phase 1 spec:** `/spec "Define User model, ShortUrl model, database schema, and sqlc queries"`

---

## Quick Commands

| Command | Purpose |
|---------|---------|
| `source venv/bin/activate` | Activate venv |
| `docker-compose up -d` | Start services |
| `python -m uvicorn app.main:app --reload` | Run app |
| `pytest` | Run tests |
| `ruff format app/ tests/` | Format code |
| `ruff check app/` | Lint |
| `mypy app/` | Type check |
| `docker-compose logs -f app` | Watch app logs |

---

**Ready?** Run `docker-compose up -d && python -m uvicorn app.main:app --reload`
