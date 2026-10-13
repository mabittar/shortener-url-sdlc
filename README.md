# URL Shortener API

A high-performance REST API service for creating and managing shortened URLs. Built with FastAPI, PostgreSQL, and Redis.

**Backend only** — Designed for third-party clients to integrate via REST API.

## Project Structure

```
shortener-url/
├── src/                    # Application source code
│   └── shortener_url/
│       ├── __init__.py
│       ├── main.py         # FastAPI application entry point
│       ├── config.py       # Configuration management
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas (request/response)
│       ├── api/            # API routes
│       └── db/             # Database utilities
├── tests/                  # Test files
├── sql/                    # SQL queries (for sqlc)
├── venv/                   # Virtual environment (git ignored)
├── .env                    # Environment variables (git ignored)
├── .env.example            # Example environment variables
├── pyproject.toml          # Project configuration
├── ruff.toml               # Ruff configuration
└── README.md               # This file
```

## Setup

### Prerequisites
- Python 3.13+
- pip (latest)
- PostgreSQL (for production)

### Installation

1. Clone the repository:
```bash
cd shortener-url
```

2. Create and activate virtual environment:
```bash
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"  # Development
# or
pip install -e .         # Production
pip install -e ".[test]" # Testing
```

4. Copy environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration.

## Development

### Running Tests
```bash
pytest
```

### Code Quality

Lint with ruff:
```bash
ruff check src/ tests/
```

Format with ruff:
```bash
ruff format src/ tests/
```

Run type checking:
```bash
mypy src/
```

### Running the Application
```bash
uvicorn src.shortener_url.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Database

Using SQLc for type-safe SQL queries:

1. Define your SQL queries in `sql/` directory
2. Generate Python code:
```bash
sqlc generate
```

## API Documentation

Once the server is running, open:
- **Swagger UI (interactive):** http://localhost:8000/docs
- **ReDoc (static):** http://localhost:8000/redoc

### Quick Examples

**Create short URL:**
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"long_url": "https://example.com/very/long/path"}'
```

**Redirect to original:**
```bash
curl -L http://localhost:8000/abc123
# Follows 302 redirect to original URL
```

**View metrics:**
```bash
curl http://localhost:8000/shorten/abc123/metrics \
  -H "X-API-Key: your-api-key"
```

## License

MIT
