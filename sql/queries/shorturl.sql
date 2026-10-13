-- Phase 1: ShortUrl CRUD + Redirect Queries
-- SQLC generates type-safe Python functions from these

-- ============================================================================
-- ShortUrl CRUD
-- ============================================================================

-- name: CreateShortUrl :one
INSERT INTO short_urls (user_id, original_url, short_code, expires_at, created_at, updated_at)
VALUES ($1, $2, $3, NOW() + INTERVAL '1 month', NOW(), NOW())
RETURNING id, short_code, original_url, created_at;

-- name: GetShortUrlByCode :one
SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE short_code = $1
  AND is_active = true
  AND (expires_at IS NULL OR expires_at > NOW());

-- name: GetShortUrlById :one
SELECT id, user_id, original_url, short_code, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE id = $1 AND is_active = true;

-- name: IncrementClickCount :exec
UPDATE short_urls
SET click_count = click_count + 1, updated_at = NOW()
WHERE id = $1;

-- name: SoftDeleteShortUrl :exec
UPDATE short_urls
SET is_active = false, updated_at = NOW()
WHERE id = $1 AND user_id = $2;

-- name: GetUserShortUrls :many
SELECT id, short_code, original_url, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE user_id = $1 AND is_active = true
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;

-- name: GetShortUrlsByUser :many
SELECT id, short_code, original_url, click_count, created_at, expires_at, is_active
FROM short_urls
WHERE user_id = $1 AND is_active = true
ORDER BY created_at DESC;

-- name: CountUserShortUrls :one
SELECT COUNT(*) as count
FROM short_urls
WHERE user_id = $1 AND is_active = true;
