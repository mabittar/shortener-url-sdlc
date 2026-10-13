# Phase 5: Observability with OTEL & LGTM Stack Specification

## LGTM Stack Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Loki** | Log aggregation (stores structured logs from FastAPI) | 3100 |
| **Grafana** | Visualization dashboard (logs, metrics, traces) | 3000 |
| **Tempo** | Distributed tracing (OpenTelemetry traces) | 3200 |
| **Mimir** | Metrics storage (Prometheus-compatible) | 9009 |
| **Promtail** | Log shipper (sends app logs to Loki) | 9080 |

---

## OpenTelemetry Instrumentation

### FastAPI Instrumentation
```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Setup tracer
tracer_provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
```

### Database Instrumentation (Psycopg3)
```python
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Instrument SQLAlchemy (if used with ORM)
SQLAlchemyInstrumentor().instrument(engine_creator=engine)

# OR for SQLC (manual span creation)
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

async def get_user_by_email(email: str):
    with tracer.start_as_current_span("db.query.get_user_by_email") as span:
        span.set_attribute("db.email", email)
        result = await db.get_user_by_email(email)
        span.set_attribute("db.rows_returned", 1 if result else 0)
        return result
```

### Redis Instrumentation
```python
from opentelemetry.instrumentation.redis import RedisInstrumentor

RedisInstrumentor().instrument()
```

### Custom Business Metrics
```python
from opentelemetry.metrics import get_meter

meter = get_meter(__name__)

# Create metrics
short_urls_created_counter = meter.create_counter(
    "short_urls.created.total",
    unit="1",
    description="Total short URLs created"
)

redirects_counter = meter.create_counter(
    "redirects.total",
    unit="1",
    description="Total redirects"
)

login_attempts_counter = meter.create_counter(
    "auth.login.attempts.total",
    unit="1",
    description="Total login attempts",
    attributes={"status": "success|failure"}
)

# Usage
short_urls_created_counter.add(1, {"user_id": user_id})
redirects_counter.add(1, {"short_code": short_code})
login_attempts_counter.add(1, {"status": "success"})
```

---

## Structured JSON Logging

### Configuration (uvicorn + custom loggers)
```python
import json
import logging
from pythonjsonlogger import jsonlogger

# JSON formatter for all loggers
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

# Root logger
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# FastAPI logger
logging.getLogger("fastapi").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
```

### Log Format (JSON)
```json
{
  "timestamp": "2026-10-12T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.controllers.auth",
  "message": "User login successful",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "user@example.com",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "duration_ms": 145,
  "trace_id": "abc123def456...",
  "span_id": "xyz789..."
}
```

### Log Levels by Endpoint
| Event | Level | Fields |
|-------|-------|--------|
| User signup | INFO | user_id, email, timestamp |
| Login success | INFO | user_id, email, ip_address, duration_ms |
| Login failure | WARN | email, reason (invalid_creds, locked), ip_address |
| Auth rate limit lock | WARN | email, lockout_duration |
| URL created | INFO | user_id, short_code, original_url_length |
| URL redirect | INFO | short_code, click_count, duration_ms |
| Error | ERROR | error_type, message, stack_trace, trace_id |

---

## Prometheus Metrics Endpoint

### Metrics to Export
```
# Counter metrics
short_urls_created_total{user_id="...",status="success"}
redirects_total{short_code="...",status="found|not_found|expired"}
auth_login_attempts_total{status="success|failure|locked"}
auth_password_resets_total{status="success|failure"}
auth_signup_attempts_total{status="success|failure"}

# Gauge metrics
active_short_urls{user_id="..."}
cache_hit_rate{endpoint="/shorten"}

# Histogram metrics (latency)
http_request_duration_seconds{method="GET",endpoint="/{short_code}",status_code="302"}
db_query_duration_seconds{operation="get_user_by_email"}
redis_operation_duration_seconds{operation="get"}
```

### Endpoint Configuration
```python
from prometheus_client import generate_latest, CollectorRegistry, Counter, Histogram

registry = CollectorRegistry()

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(registry), media_type="text/plain")
```

---

## Distributed Tracing with Tempo

### Trace Sampling
- **Development:** 100% sampling (all traces)
- **Production:** 10% sampling (every 10th trace) or adaptive

### Span Attributes
```python
# For each API request
span.set_attribute("http.method", "POST")
span.set_attribute("http.url", "/shorten")
span.set_attribute("http.status_code", 201)
span.set_attribute("http.client_ip", request.client.host)
span.set_attribute("user_id", user_id)

# Database spans
span.set_attribute("db.operation", "query")
span.set_attribute("db.table", "users")
span.set_attribute("db.rows_affected", 1)
span.set_attribute("db.duration_ms", 45)

# Cache spans
span.set_attribute("cache.operation", "get")
span.set_attribute("cache.key", "shorturl:abc123")
span.set_attribute("cache.hit", True)
```

### Trace Collection
```
FastAPI app
    ↓ (OTLP gRPC on port 4317)
Tempo
    ↓
Grafana (visualize traces)
```

---

## Grafana Dashboards

### Dashboard 1: Application Overview
- **Panels:**
  - Request rate (req/s)
  - Error rate (%)
  - P50, P95, P99 latency
  - Active users
  - Cache hit rate

### Dashboard 2: Authentication Metrics
- **Panels:**
  - Login success/failure rates
  - Rate limit locks per hour
  - Signup rate
  - Password reset requests

### Dashboard 3: URL Shortening Performance
- **Panels:**
  - URLs created per hour
  - Redirect latency (p99)
  - Cache hit rate
  - Redirect throughput (req/s)

### Dashboard 4: Infrastructure
- **Panels:**
  - Postgres connection pool utilization
  - Redis memory usage
  - Disk I/O
  - CPU usage
  - Network I/O

### Dashboard 5: Distributed Traces
- **Type:** Tempo data source
- **Views:**
  - Trace search by service, operation, duration
  - Critical path analysis
  - Latency distribution
  - Dependency graph (FastAPI → DB → Redis)

---

## Loki Log Queries (LogQL)

### Examples
```
# All errors
{job="shortener-app"} | json | level="ERROR"

# Login attempts by status
{job="shortener-app"} | json | logger="app.controllers.auth" | status="success|failure"

# Slow requests (> 1 second)
{job="shortener-app"} | json | duration_ms > 1000

# Specific user
{job="shortener-app"} | json | user_id="a1b2c3d4-e5f6..."

# Rate limit locks
{job="shortener-app"} | json | level="WARN" | message="rate_limit_lock"
```

---

## Alert Rules (Mimir + Grafana Alerting)

### Alert 1: High Error Rate
```
alert: HighErrorRate
expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
for: 5m
labels:
  severity: critical
annotations:
  summary: "High error rate detected"
```

### Alert 2: Database Connection Pool Exhaustion
```
alert: DBConnectionPoolExhausted
expr: pg_stat_activity_count >= 90
for: 2m
labels:
  severity: critical
```

### Alert 3: Redis Memory Usage
```
alert: RedisHighMemory
expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
for: 5m
labels:
  severity: warning
```

### Alert 4: Slow Redirect Latency
```
alert: SlowRedirectLatency
expr: histogram_quantile(0.99, http_request_duration_seconds{endpoint="/{short_code}"}) > 0.1
for: 5m
labels:
  severity: warning
```

---

## Docker Compose Integration

Add to `docker-compose.yml`:

```yaml
services:
  loki:
    image: grafana/loki:3.0.0
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml

  tempo:
    image: grafana/tempo:2.3.0
    ports:
      - "3200:3200"
      - "4317:4317"  # OTLP gRPC receiver
    volumes:
      - tempo_data:/var/tempo

  mimir:
    image: grafana/mimir:2.10.0
    ports:
      - "9009:9009"
    volumes:
      - mimir_data:/data

  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning  # Dashboards
    depends_on:
      - loki
      - tempo
      - mimir

volumes:
  loki_data:
  tempo_data:
  mimir_data:
  grafana_data:
```

---

## Acceptance Criteria

### OTEL Instrumentation
- [ ] FastAPI instrumented (all requests traced)
- [ ] Database queries traced (operation, table, duration)
- [ ] Redis operations traced (operation, key, hit/miss)
- [ ] Custom business metrics (URLs created, redirects, logins)
- [ ] Traces exported to Tempo (OTLP gRPC on :4317)

### Structured Logging
- [ ] All logs in JSON format (timestamp, level, message, context)
- [ ] Trace ID / Span ID included in all logs
- [ ] Sensitive data redacted (passwords, API keys)
- [ ] Log levels appropriate (DEBUG, INFO, WARN, ERROR)
- [ ] Logs shipped to Loki

### Grafana Dashboards
- [ ] 5 dashboards configured (overview, auth, shortening, infra, traces)
- [ ] All metrics displayed and updated in real-time
- [ ] Alerts configured (errors, DB exhaustion, Redis memory, latency)

### Prometheus Metrics
- [ ] Endpoint at GET /metrics (Prometheus format)
- [ ] Counter metrics (requests, errors, creates)
- [ ] Gauge metrics (active URLs, cache hit rate)
- [ ] Histogram metrics (latency distributions)
- [ ] Mimir scrapes metrics every 15s

---

## Spec Output Command

```bash
/spec "Phase 5: Implement OpenTelemetry instrumentation (FastAPI, database queries, Redis operations, custom metrics). Setup LGTM stack (Loki for logs, Grafana for dashboards, Tempo for traces, Mimir for metrics). Structured JSON logging with trace IDs. Export OTLP traces to Tempo on :4317. Prometheus metrics endpoint at GET /metrics. 5 Grafana dashboards (overview, auth, shortening, infrastructure, traces). Alert rules for errors, DB exhaustion, Redis memory, latency."
```

Output: `docs/specs/YYYYMMDD-PHASE5-OBSERVABILITY_spec.md`

---

## Stack Summary

```
App (FastAPI + OTEL SDK)
  ├─ Logs (JSON) → Loki (:3100)
  ├─ Traces (OTLP gRPC) → Tempo (:3200, :4317)
  └─ Metrics (Prometheus) → Mimir (:9009)
       ↓
    Grafana (:3000)
    ├─ Dashboard 1: Overview
    ├─ Dashboard 2: Auth
    ├─ Dashboard 3: Shortening
    ├─ Dashboard 4: Infrastructure
    └─ Dashboard 5: Traces (Tempo)
```

---

**Next:** Create Phase 5 spec with this detailed observability design.
