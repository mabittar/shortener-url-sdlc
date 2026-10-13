# Phase 1: Foundation Specification Template

## Key Requirements

### User Model (UUID v7 Primary Key)
- `id` (UUID v7, PK, native PostgreSQL 18)
- `email` (VARCHAR(255), unique, not null)
- `password_hash` (VARCHAR(255), bcrypt-hashed, not null)
- `api_key` (VARCHAR(64), unique, auto-generated on signup)
- `name` (VARCHAR(255), optional)
- `email_verified` (BOOL, default false)
- `password_reset_token` (VARCHAR(255), nullable) — for magic-link
- `password_reset_expires` (TIMESTAMP, nullable) — TTL 15 minutes
- `created_at` (TIMESTAMP, default now())
- `updated_at` (TIMESTAMP, default now())
- `is_active` (BOOL, default true)

### ShortUrl Model
- `id` (UUID v7, PK)
- `user_id` (UUID v7, FK → User.id, not null) — owner
- `original_url` (TEXT, not null) — full URL
- `short_code` (VARCHAR(16), unique, not null) — Algorithm: base62(user_id[:5] + random_6_10_digits)
  - Example: user_id = `a1b2c3d4-e5f6...` → `a1b2c` + `3x4y5z` = `a1b2c3x4y5z`
- `click_count` (INT, default 0)
- `created_at` (TIMESTAMP, default now())
- `updated_at` (TIMESTAMP, default now())
- `expires_at` (TIMESTAMP, default now() + interval '1 month')
- `is_active` (BOOL, default true) — soft delete

### Indices
- `users(email)` — unique, for login lookup
- `users(api_key)` — unique, for auth validation
- `short_urls(short_code)` — unique, for redirect lookup
- `short_urls(user_id)` — for user's URLs listing
- `short_urls(is_active)` — for filtering active URLs

---

## SQLC Queries to Generate

### User Queries
```sql
-- name: CreateUser :one
INSERT INTO users (email, password_hash, api_key, name, created_at, updated_at)
VALUES ($1, $2, $3, $4, NOW(), NOW())
RETURNING id, email, api_key, created_at;

-- name: GetUserByEmail :one
SELECT id, email, password_hash, api_key, email_verified, is_active
FROM users WHERE email = $1 AND is_active = true;

-- name: GetUserByApiKey :one
SELECT id, email, api_key, is_active
FROM users WHERE api_key = $1 AND is_active = true;

-- name: UpdateUserPassword :exec
UPDATE users SET password_hash = $1, updated_at = NOW()
WHERE id = $2;

-- name: SetPasswordResetToken :exec
UPDATE users SET password_reset_token = $1, password_reset_expires = NOW() + interval '15 minutes'
WHERE id = $2;

-- name: GetUserByPasswordResetToken :one
SELECT id, email FROM users
WHERE password_reset_token = $1 
  AND password_reset_expires > NOW() 
  AND is_active = true;

-- name: ClearPasswordResetToken :exec
UPDATE users SET password_reset_token = NULL, password_reset_expires = NULL
WHERE id = $1;
```

### ShortUrl Queries
```sql
-- name: CreateShortUrl :one
INSERT INTO short_urls (user_id, original_url, short_code, expires_at, created_at, updated_at)
VALUES ($1, $2, $3, NOW() + interval '1 month', NOW(), NOW())
RETURNING id, short_code, original_url, created_at;

-- name: GetShortUrlByCode :one
SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE short_code = $1 AND is_active = true AND (expires_at IS NULL OR expires_at > NOW());

-- name: GetShortUrlById :one
SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE id = $1 AND is_active = true;

-- name: IncrementClickCount :exec
UPDATE short_urls SET click_count = click_count + 1, updated_at = NOW()
WHERE id = $1;

-- name: GetUserShortUrls :many
SELECT id, short_code, original_url, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE user_id = $1 AND is_active = true
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;

-- name: SoftDeleteShortUrl :exec
UPDATE short_urls SET is_active = false, updated_at = NOW()
WHERE id = $1 AND user_id = $2;
```

---

## Acceptance Criteria

### Database Schema
- [ ] PostgreSQL 18 with UUID v7 extension
- [ ] users table with all fields
- [ ] short_urls table with user_id FK
- [ ] Indices created (email, api_key, short_code, user_id, is_active)
- [ ] Foreign key constraint: short_urls.user_id → users.id

### SQLC Generation
- [ ] All queries compile without errors
- [ ] Generated Python code in `app/db/sqlc/`
- [ ] Type annotations correct (e.g., CreateUserResult, GetUserByEmailRow)
- [ ] No SQL injection vulnerabilities

### Validation
- [ ] Email format validation (Pydantic)
- [ ] Password minimum strength (e.g., 8 chars, mix of types)
- [ ] api_key generated as random 64-character hex string
- [ ] short_code format: user_id[:5] + 6-10 random digits → base62

---

## Spec Output Commands

When ready to write the full spec, use:

```bash
/spec "Phase 1: Define User model (UUID v7 PK, email unique, password_hash bcrypt, api_key), ShortUrl model (user_id FK, short_code=base62(user_id[:5]+random)), PostgreSQL 18 schema with indices, SQLC queries for CRUD + auth + shorturl operations"
```

This will produce `docs/specs/YYYYMMDD-PHASE1-FOUNDATION_spec.md` with:
- Objective
- Functional Description
- Technical Flow (signup → user created → api_key generated)
- Acceptance Criteria (Gherkin scenarios)
- Database schema details
- SQLC query definitions
- Solution Design (Mermaid ER diagram)
