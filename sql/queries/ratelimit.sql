-- Phase 1: Rate Limiting Queries (Stubs for Phase 1.5 Logic)
-- Real-time rate limiting in Redis; audit trail in PostgreSQL

-- ============================================================================
-- URL Creation Throttle (1 URL per minute per user)
-- ============================================================================

-- name: RecordUrlCreation :exec
INSERT INTO url_creation_throttle (user_id, minute_bucket, count, created_at)
VALUES ($1, DATE_TRUNC('minute', NOW()), 1, NOW());

-- name: GetUrlCreationCount :one
SELECT COUNT(*) as count
FROM url_creation_throttle
WHERE user_id = $1
  AND minute_bucket = DATE_TRUNC('minute', NOW());

-- name: ClearUrlCreationThrottle :exec
DELETE FROM url_creation_throttle
WHERE minute_bucket < NOW() - INTERVAL '1 minute';

-- ============================================================================
-- Login Rate Limiting (3 failed attempts → 5 min lockout)
-- ============================================================================

-- name: SetLoginLockout :exec
UPDATE failed_login_attempts
SET locked_until = NOW() + INTERVAL '5 minutes'
WHERE email = $1;

-- name: IsLoginLocked :one
SELECT locked_until > NOW() as is_locked
FROM failed_login_attempts
WHERE email = $1;

-- name: ResetLoginAttempts :exec
UPDATE failed_login_attempts
SET attempt_count = 0, locked_until = NULL, updated_at = NOW()
WHERE email = $1;
