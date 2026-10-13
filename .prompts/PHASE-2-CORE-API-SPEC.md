# Phase 2: Core API Specification Template

## Key Requirements

### Endpoints to Implement

#### POST /shorten — Create Short URL
```
Authentication: Required (X-API-Key header)
Rate Limit: 1 URL per minute per user (429 Too Many Requests if exceeded)

Request:
  {
    "long_url": "https://example.com/very/long/path/with/parameters?foo=bar&baz=qux",
    "custom_url": null  # Optional (Phase 3), ignored in Phase 2
  }

Response (201 Created):
  {
    "id": "b2c3d4e5-f6g7-8901-hijk-lm2345678901",
    "short_code": "a1b2c3x4y5z",  # base62(user_id[:5] + random)
    "short_url": "https://api.example.com/a1b2c3x4y5z",
    "original_url": "https://example.com/very/long/path/...",
    "click_count": 0,
    "expires_at": "2026-11-12T10:30:00Z",  # +1 month
    "created_at": "2026-10-12T10:30:00Z"
  }

Headers:
  Location: https://api.example.com/a1b2c3x4y5z

Errors:
  - 400 Bad Request: invalid long_url (not a valid URL)
  - 401 Unauthorized: missing or invalid API Key
  - 429 Too Many Requests: exceeded 1 URL/minute limit (include Retry-After header)
  - 422 Unprocessable Entity: long_url is too long (> 2000 chars)
```

#### GET /{short_code} — Redirect to Original URL
```
Authentication: None (public endpoint)

Request:
  GET /a1b2c3x4y5z

Response (302 Found):
  Location: https://example.com/very/long/path/with/parameters?foo=bar&baz=qux
  
  # Browser follows redirect to original URL
  # Server tracks click: increment short_urls.click_count

Side Effects:
  1. Validate short_code exists and is_active = true
  2. Check if expired (expires_at > NOW())
  3. If valid: increment click_count asynchronously
  4. Return 302 with Location header
  5. Optional: track click in analytics table (Phase 3)

Errors:
  - 404 Not Found: short_code not found or expired
  - 410 Gone: short_code exists but is soft-deleted (is_active = false)
```

---

## Short Code Generation Algorithm

**Format:** base62(user_id[:5] + random_digits)

### Steps:
1. Extract first 5 characters from user_id
   - Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890` → `a1b2c`
2. Generate 6-10 random digits (0-9)
   - Example: `3x4y5z`
3. Concatenate: `a1b2c` + `3x4y5z` = `a1b2c3x4y5z`
4. Encode as base62 (alphanumeric: 0-9, a-z, A-Z)
5. Store in short_urls.short_code (VARCHAR(16), unique)

### Uniqueness:
- **Total combinations:** 5 chars (user prefix) + 6-10 random → ~billions of combinations
- **Collision handling:** Check uniqueness in DB before insert
- **Retry:** If collision, regenerate random part and retry (max 3 attempts)

---

## Rate Limiting (URL Creation)

**Policy:** 1 URL per minute per user

### Implementation:
1. Track URLs created per user per minute
   - Use Redis: key = `rate_limit:shorten:{user_id}:{minute}`, value = count
   - TTL = 60 seconds
2. On POST /shorten:
   - Check Redis counter for current minute
   - If count >= 1: return 429
   - Else: increment counter, create URL, return 201
3. Return response:
   - Status: 429 Too Many Requests
   - Header: `Retry-After: 60`
   - Body: `{ "message": "Rate limit exceeded. Max 1 URL per minute." }`

### Alternative (if Redis unavailable):
- Use database table: `rate_limits(user_id, minute, count, created_at)`
- Query last minute's count
- Cleanup old records periodically

---

## Acceptance Criteria

### POST /shorten
- [ ] Validates long_url is a valid URL (regex or urllib.parse)
- [ ] Validates long_url length (max 2000 chars)
- [ ] Extracts user from API Key (from request header)
- [ ] Generates short_code = base62(user_id[:5] + random)
- [ ] Checks uniqueness in database
- [ ] Creates ShortUrl record with expires_at = NOW() + 1 month
- [ ] Returns 201 with Location header
- [ ] Rate limit: 1 per minute per user (429 if exceeded)

### GET /{short_code}
- [ ] Queries short_urls by short_code
- [ ] Checks is_active = true
- [ ] Checks expires_at > NOW()
- [ ] Returns 302 Found with original URL in Location header
- [ ] Increments click_count (can be async)
- [ ] Returns 404 if not found
- [ ] Returns 410 if soft-deleted

### Error Handling
- [ ] 400: Invalid URL format
- [ ] 401: Missing/invalid API Key
- [ ] 404: Short code not found
- [ ] 410: Short code deleted
- [ ] 422: Invalid input (too long, etc.)
- [ ] 429: Rate limit exceeded

### Performance
- [ ] Redirect latency (without Redis): < 100ms p99
- [ ] Redirect latency (with Redis cache, Phase 4): < 50ms p99

---

## API Key Authentication Mechanism

### Header-based Auth
```
Request:
  GET /shorten
  Headers:
    X-API-Key: sk_live_abc123def456ghi789...

Validation:
  1. Extract X-API-Key from header
  2. Query users.api_key = provided_key
  3. If found: user is authenticated
  4. If not found: return 401
  5. If user.is_active = false: return 403
```

### SQLC Query
```sql
-- name: GetUserByApiKey :one
SELECT id, email, api_key, is_active
FROM users WHERE api_key = $1 AND is_active = true;
```

---

## Spec Output Command

```bash
/spec "Phase 2: Implement POST /shorten (requires X-API-Key auth, generates short_code=base62(user_id[:5]+random), rate limit 1 per minute, return 201) and GET /{short_code} (public, no auth, return 302 redirect to original URL, track click count increment, 404 if not found or expired)"
```

This will produce `docs/specs/YYYYMMDD-PHASE2-CORE-API_spec.md` with:
- Objective (enable URL creation and redirection)
- Functional Description (create, redirect flows)
- Technical Flow (POST validation → generate → store; GET lookup → redirect → track)
- Acceptance Criteria (Gherkin for both endpoints)
- Rate Limiting (1 URL/min per user)
- Short Code Algorithm (base62 with uniqueness)
- Solution Design (Mermaid flow diagram)
- Definition of Done (tests, docs, error handling)
