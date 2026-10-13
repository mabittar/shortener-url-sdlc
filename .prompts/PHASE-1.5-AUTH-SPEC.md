# Phase 1.5: User Authentication Specification Template

## Key Requirements

### Endpoints to Implement

#### POST /auth/signup
```
Request:
  {
    "email": "user@example.com",
    "password": "SecurePassword123",
    "name": "John Doe" (optional)
  }

Response (201 Created):
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "user@example.com",
    "name": "John Doe",
    "api_key": "<sk_live_placeholder>",
    "created_at": "2026-10-12T10:30:00Z"
  }

Errors:
  - 400 Bad Request: email already exists
  - 400 Bad Request: password too weak
  - 422 Unprocessable Entity: invalid email format
```

#### POST /auth/login
```
Request:
  {
    "email": "user@example.com",
    "password": "SecurePassword123"
  }

Response (200 OK):
  {
    "api_key": "<sk_live_placeholder>",
    "user": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "user@example.com",
      "name": "John Doe"
    }
  }

Errors:
  - 401 Unauthorized: invalid email or password
  - 403 Forbidden: account disabled (is_active = false)
  - 429 Too Many Requests: too many failed attempts (locked for 5 min)
    - Response header: `Retry-After: 300`
    - Body: { "message": "Too many failed attempts. Try again in 5 minutes." }
```

#### POST /auth/password-reset-request
```
Request:
  {
    "email": "user@example.com"
  }

Response (200 OK):
  {
    "message": "Password reset link sent to email",
    "email": "user@example.com"
  }

Side Effect:
  - Generate reset_token (random 32-char hex)
  - Set password_reset_expires = NOW() + 15 minutes
  - Send email with magic-link: https://app.example.com/reset?token=XXXXX
    (Email sending is OUT OF SCOPE — assume email service integrates later)

Errors:
  - 404 Not Found: email not found
```

#### POST /auth/password-reset
```
Request:
  {
    "reset_token": "abc123def456ghi789jkl012mno345pq",
    "new_password": "NewSecurePassword456"
  }

Response (200 OK):
  {
    "message": "Password reset successfully"
  }

Steps:
  1. Validate reset_token exists and not expired (< 15 min)
  2. Hash new_password with bcrypt
  3. Update user.password_hash
  4. Clear reset_token and reset_expires
  5. Invalidate existing sessions (if any)

Errors:
  - 400 Bad Request: token expired
  - 400 Bad Request: token invalid
  - 422 Unprocessable Entity: password too weak
```

---

## Password Requirements

- **Minimum length:** 8 characters
- **Character mix:** At least one uppercase, one lowercase, one digit
- **No common patterns:** "password", "123456", sequential numbers
- **Hash function:** bcrypt with salt (bcrypt.hashpw)
- **Cost factor:** 12 (balance between security and speed)

---

## API Key Generation

- **Format:** `<sk_live_placeholder>` + 32 random hex characters
- **Length:** ~40 characters total
- **Storage:** Stored in `users.api_key` as plaintext (can be hashed in Phase 3)
- **Usage:** Header `X-API-Key: <sk_live_placeholder>...` on protected endpoints

---

## Acceptance Criteria

### User Signup
- [ ] Email validation (RFC 5322 simplified, no DNS check)
- [ ] Password hashing with bcrypt (cost = 12)
- [ ] API key generated and stored
- [ ] User created with is_active = true
- [ ] Duplicate email returns 400
- [ ] Weak password returns 422

### User Login
- [ ] Email + password verified against password_hash
- [ ] Invalid credentials return 401 (generic message, no user existence leak)
- [ ] Disabled account (is_active = false) returns 403
- [ ] Successful login returns api_key + user data

### Password Reset Flow
- [ ] Reset token generation (32-char random hex)
- [ ] Reset token expires after 15 minutes
- [ ] Token validated before password update
- [ ] Expired token rejected with 400
- [ ] Invalid token rejected with 400
- [ ] Password updated + token cleared

### Rate Limiting (Authentication)
- [ ] Track failed login attempts per email (in Redis or database)
- [ ] 3 failed attempts → lock for 5 minutes
- [ ] Lock applies to all login attempts for that email (regardless of password)
- [ ] After 5 minutes, reset attempt counter to 0
- [ ] Successful login → reset attempt counter to 0
- [ ] Return 429 Too Many Requests when locked (include Retry-After: 300 seconds)

### Security
- [ ] Never log passwords or password_hash
- [ ] Never expose password_hash in API responses
- [ ] API key returned only on signup, NOT on login (return on signup, hide on login to prevent leaks)
- [ ] Rate limiting on login attempts (3 failed → 5 min lockout)
- [ ] HTTPS in production (enforced at load balancer)

---

## Spec Output Command

```bash
/spec "Phase 1.5: Implement user authentication endpoints (signup: email+password→create user+api_key, login: email+password→return api_key, password-reset-request: email→generate magic-link, password-reset: token+new_password→update password). Password hashing with bcrypt (cost 12), reset token TTL 15 min, API key = <sk_live_placeholder>+32hex"
```

This will produce `docs/specs/YYYYMMDD-PHASE1.5-AUTH_spec.md` with:
- Objective (enable user authentication)
- Functional Description (signup, login, password reset flows)
- Technical Flow (request → validation → hashing → storage)
- Acceptance Criteria (Gherkin for each endpoint)
- Security Considerations (bcrypt, rate limiting strategy, etc.)
- Solution Design (Mermaid auth flow diagram)
- Definition of Done (tests, migrations, docs)
