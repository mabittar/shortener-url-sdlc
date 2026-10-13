-- Phase 1: User CRUD + Authentication Queries
-- SQLC generates type-safe Python functions from these

-- ============================================================================
-- User CRUD
-- ============================================================================

-- name: CreateUser :one
INSERT INTO users (email, password_hash, api_key, name, created_at, updated_at)
VALUES ($1, $2, $3, $4, NOW(), NOW())
RETURNING id, email, api_key, created_at;

-- name: GetUserByEmail :one
SELECT id, email, password_hash, api_key, email_verified, is_active
FROM users
WHERE email = $1 AND is_active = true;

-- name: GetUserByApiKey :one
SELECT id, email, api_key, is_active
FROM users
WHERE api_key = $1 AND is_active = true;

-- name: GetUserById :one
SELECT id, email, name, api_key, created_at
FROM users
WHERE id = $1 AND is_active = true;

-- name: UpdateUserPassword :exec
UPDATE users
SET password_hash = $1, updated_at = NOW()
WHERE id = $2;

-- ============================================================================
-- Password Reset Flow
-- ============================================================================

-- name: SetPasswordResetToken :exec
UPDATE users
SET password_reset_token = $1,
    password_reset_expires = NOW() + INTERVAL '15 minutes'
WHERE id = $2;

-- name: GetUserByPasswordResetToken :one
SELECT id, email
FROM users
WHERE password_reset_token = $1
  AND password_reset_expires > NOW()
  AND is_active = true;

-- name: ClearPasswordResetToken :exec
UPDATE users
SET password_reset_token = NULL, password_reset_expires = NULL
WHERE id = $1;

-- ============================================================================
-- Rate Limiting: Failed Login Attempts
-- ============================================================================

-- name: RecordFailedLoginAttempt :exec
INSERT INTO failed_login_attempts (email, attempt_count, created_at, updated_at)
VALUES ($1, 1, NOW(), NOW())
ON CONFLICT (email) DO UPDATE
SET attempt_count = failed_login_attempts.attempt_count + 1,
    updated_at = NOW();

-- name: GetFailedLoginAttempts :one
SELECT email, attempt_count, locked_until
FROM failed_login_attempts
WHERE email = $1;

-- name: ClearFailedLoginAttempts :exec
DELETE FROM failed_login_attempts
WHERE email = $1;
