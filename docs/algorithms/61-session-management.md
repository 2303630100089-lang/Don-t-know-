# 61. Algorithm: Session Management

## Overview

Secure session management algorithm covering user login, Redis-based token storage, fast validation, inactivity-based expiry, and secure refresh mechanisms.

## Algorithm Steps

### Step 1: User Login → Session Token
- User authenticates with credentials (password, OAuth, MFA).
- Server generates cryptographically secure session token.
- Token format: opaque random string (256-bit entropy) or JWT.
- Session metadata created: user_id, roles, device_info, IP, login_time.
- Token returned to client via secure HttpOnly cookie or response body.

### Step 2: Token Stored in Redis
- Session data stored in Redis with token as key.
- Data structure: Redis hash for efficient field-level access.
- Redis key: `session:{token_hash}` (token hashed for security).
- Session data: user_id, roles, permissions, device, IP, created_at, last_active.
- Redis cluster for high availability and horizontal scaling.

### Step 3: Fast Validation
- Every API request includes session token.
- Token hash computed and looked up in Redis (O(1) operation).
- Local in-memory cache for repeated validations (LRU, TTL: 30s).
- Validation checks: exists, not expired, IP consistency (optional).
- Validation latency: < 1ms (cached), < 3ms (Redis lookup).

### Step 4: Expiry After Inactivity
- Each successful validation extends session TTL (sliding expiry).
- Default inactivity timeout: 30 minutes.
- Absolute session lifetime: 24 hours (requires re-authentication).
- Redis TTL automatically removes expired sessions.
- Configurable per user role (admin: 15min, user: 30min).

### Step 5: Secure Refresh Mechanism
- Refresh token issued alongside session token (longer-lived).
- Refresh token stored separately with stricter validation.
- On session expiry, client sends refresh token to get new session.
- Refresh token rotated on each use (one-time use).
- Refresh token family tracking: detect reuse → revoke all sessions.

## Pseudocode

```
function login(credentials):
    user = authenticate(credentials)
    if not user:
        throw AuthenticationError
    
    // Generate tokens
    session_token = generateSecureRandom(256 bits)
    refresh_token = generateSecureRandom(256 bits)
    
    session_data = {
        user_id: user.id,
        roles: user.roles,
        permissions: user.permissions,
        device: request.device_info,
        ip: request.ip,
        created_at: now(),
        last_active: now(),
        refresh_family: generateId()
    }
    
    // Store in Redis
    token_hash = sha256(session_token)
    redis.hset(f"session:{token_hash}", session_data)
    redis.expire(f"session:{token_hash}", INACTIVITY_TIMEOUT)
    
    refresh_hash = sha256(refresh_token)
    redis.hset(f"refresh:{refresh_hash}", {
        user_id: user.id,
        family: session_data.refresh_family,
        used: false
    })
    redis.expire(f"refresh:{refresh_hash}", REFRESH_TOKEN_LIFETIME)
    
    return { session_token, refresh_token }

function validateSession(session_token):
    token_hash = sha256(session_token)
    
    // Check local cache first
    cached = localCache.get(token_hash)
    if cached and cached.valid:
        return cached.session_data
    
    // Redis lookup
    session_data = redis.hgetall(f"session:{token_hash}")
    if not session_data:
        throw SessionExpiredError
    
    // Extend TTL (sliding expiry)
    redis.expire(f"session:{token_hash}", INACTIVITY_TIMEOUT)
    session_data.last_active = now()
    redis.hset(f"session:{token_hash}", "last_active", now())
    
    // Update local cache
    localCache.set(token_hash, session_data, ttl=30s)
    
    return session_data

function refreshSession(refresh_token):
    refresh_hash = sha256(refresh_token)
    refresh_data = redis.hgetall(f"refresh:{refresh_hash}")
    
    if not refresh_data:
        throw InvalidRefreshToken
    
    if refresh_data.used:
        // Token reuse detected — compromise likely
        revokeAllSessions(refresh_data.family)
        throw TokenReuseDetected
    
    // Mark as used
    redis.hset(f"refresh:{refresh_hash}", "used", true)
    
    // Issue new session + new refresh token
    return login(refresh_data.user_id)  // Simplified

function logout(session_token):
    token_hash = sha256(session_token)
    redis.del(f"session:{token_hash}")
    localCache.invalidate(token_hash)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Session creation | < 5ms |
| Validation (cached) | < 1ms |
| Validation (Redis) | < 3ms |
| Token refresh | < 10ms |
| Logout | < 2ms |
