# 47. Algorithm: File Sharing

## Overview

Secure file sharing algorithm covering upload to object storage, metadata management, tokenized URL generation, CDN distribution, and access validation.

## Algorithm Steps

### Step 1: File Upload → Object Storage
- Client uploads file via multipart upload.
- File chunked for large files (chunk size: 5MB).
- Each chunk uploaded in parallel for speed.
- Server reassembles chunks and stores in object storage (S3/GCS/MinIO).
- File integrity verified via SHA-256 checksum.

### Step 2: Metadata → DB
- File metadata stored in relational database.
- Metadata includes: file_id, name, size, mime_type, uploader_id, created_at.
- Permission records: who can view, edit, or download.
- Version history tracked for file updates.
- Tags and categories for organization.

### Step 3: Tokenized URL Generated
- Signed URL generated with cryptographic token.
- Token encodes: file_id, user_id, permissions, expiry_time.
- Token signed with HMAC-SHA256 using server secret.
- URL format: `https://cdn.example.com/files/{file_id}?token={signed_token}&expires={timestamp}`.
- Token expiry configurable (default: 1 hour).

### Step 4: CDN Distribution
- File distributed to CDN edge nodes for global access.
- Cache-Control headers set for optimal caching.
- Origin pull: CDN fetches from object storage on first request.
- Subsequent requests served from edge cache.
- Geographic routing to nearest edge node.

### Step 5: Access Validated via Token
- CDN edge validates token on each request.
- Validation checks: signature validity, expiry, user permissions.
- Invalid tokens return 403 Forbidden.
- Access logged for audit trail.
- Rate limiting per user to prevent abuse.

## Pseudocode

```
function uploadFile(user_id, file_data, filename):
    // Step 1: Upload to object storage
    file_id = generateFileId()
    checksum = sha256(file_data)
    
    chunks = splitIntoChunks(file_data, chunkSize=5MB)
    upload_promises = []
    for chunk in chunks:
        upload_promises.append(
            objectStorage.uploadChunk(file_id, chunk.index, chunk.data)
        )
    await all(upload_promises)
    objectStorage.completeMultipartUpload(file_id)
    
    // Verify integrity
    stored_checksum = objectStorage.getChecksum(file_id)
    assert stored_checksum == checksum
    
    // Step 2: Store metadata
    metadata = {
        file_id, filename, 
        size: file_data.length,
        mime_type: detectMimeType(file_data),
        uploader_id: user_id,
        checksum, 
        created_at: now()
    }
    db.storeFileMetadata(metadata)
    db.setPermission(file_id, user_id, OWNER)
    
    return file_id

function generateShareLink(file_id, user_id, target_user_id, expiry_hours=1):
    // Step 3: Generate tokenized URL
    db.setPermission(file_id, target_user_id, READ)
    
    token_data = {
        file_id, user_id: target_user_id,
        permissions: READ,
        expires: now() + hours(expiry_hours)
    }
    token = hmacSHA256(JSON.stringify(token_data), SERVER_SECRET)
    
    return f"https://cdn.example.com/files/{file_id}?token={token}&expires={token_data.expires}"

function validateAccess(file_id, token, expires):
    // Step 5: Validate token
    if now() > expires:
        return 403  // Expired
    
    expected_token = hmacSHA256(reconstructTokenData(file_id, expires), SERVER_SECRET)
    if token != expected_token:
        return 403  // Invalid signature
    
    auditLog.record(file_id, user_id, ACCESS)
    return 200  // Serve file from CDN
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Upload speed (100MB) | < 10 seconds |
| URL generation | < 5ms |
| CDN delivery latency | < 50ms |
| Token validation | < 1ms |
| Download speed | Limited by client bandwidth |
