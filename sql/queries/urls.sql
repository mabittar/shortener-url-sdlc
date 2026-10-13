-- name: GetUrlByShortCode :one
SELECT id, short_code, original_url, click_count, created_at, updated_at, expires_at, is_active
FROM urls
WHERE short_code = $1 AND is_active = true;

-- name: CreateUrl :one
INSERT INTO urls (short_code, original_url, created_at, updated_at)
VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
RETURNING id, short_code, original_url, click_count, created_at, updated_at, expires_at, is_active;

-- name: IncrementClickCount :exec
UPDATE urls
SET click_count = click_count + 1, updated_at = CURRENT_TIMESTAMP
WHERE id = $1;

-- name: DeactivateUrl :exec
UPDATE urls
SET is_active = false, updated_at = CURRENT_TIMESTAMP
WHERE id = $1;

-- name: GetAllUrls :many
SELECT id, short_code, original_url, click_count, created_at, updated_at, expires_at, is_active
FROM urls
WHERE is_active = true
ORDER BY created_at DESC
LIMIT $1 OFFSET $2;
