# 32. Workflow: Encryption

## Overview

Comprehensive encryption workflow ensuring data security at all layers — in transit, at rest, and during key exchange — with fast key rotation capabilities.

## Components

### TLS for Transport Security
- **TLS 1.3**: Latest protocol for transport encryption.
- **Certificate Management**: Automated via Let's Encrypt or internal CA.
- **Cipher Suites**: AES-256-GCM, ChaCha20-Poly1305.
- **Perfect Forward Secrecy**: ECDHE key exchange ensures past sessions remain secure.
- **Certificate Pinning**: Optional for mobile clients.

### AES-256 for Data at Rest
- **Algorithm**: AES-256 in GCM mode (authenticated encryption).
- **Key Management**: Keys stored in HSM (Hardware Security Module) or KMS.
- **Envelope Encryption**: Data encrypted with DEK (Data Encryption Key), DEK encrypted with KEK (Key Encryption Key).
- **Transparent Encryption**: Database-level and storage-level encryption.
- **Performance**: Hardware-accelerated AES-NI instructions.

### RSA for Key Exchange
- **Key Size**: RSA-4096 for key exchange operations.
- **Usage**: Encrypting symmetric keys for secure distribution.
- **Digital Signatures**: RSA-PSS for signing tokens and certificates.
- **Key Pair Management**: Automated key generation and storage.
- **Fallback**: ECDSA (P-256) as a lighter alternative.

### Hashing with SHA-256
- **Password Hashing**: bcrypt/scrypt/Argon2id (not raw SHA-256).
- **Data Integrity**: SHA-256 for checksums and data verification.
- **HMAC**: SHA-256-based HMAC for message authentication.
- **Content Addressing**: SHA-256 hashes for file deduplication.
- **Performance**: Hardware-accelerated SHA extensions.

### Fast Key Rotation Algorithm
- **Rotation Schedule**: Configurable (default 90 days for DEKs, 1 year for KEKs).
- **Zero-Downtime Rotation**: Dual-key period supports both old and new keys.
- **Automated Rotation**: Event-driven rotation via KMS APIs.
- **Re-encryption**: Background process re-encrypts data with new keys.
- **Audit**: All rotation events logged for compliance.

## Flow Diagram

```
Data Flow (In Transit)
       │
       ▼
┌──────────────┐
│   TLS 1.3   │
│  Handshake   │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  RSA Key     │────▶│   KMS/HSM    │
│  Exchange    │     │              │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│ AES-256-GCM  │
│  Encryption  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  SHA-256     │
│  Integrity   │
└──────┬───────┘
       │
       ▼
  Secure Data at Rest
       │
       ▼
┌──────────────┐
│ Key Rotation │
│  (Scheduled) │
└──────────────┘
```

## Security Standards

| Standard | Implementation |
|----------|---------------|
| FIPS 140-2 | HSM compliance |
| SOC 2 | Encryption audit trail |
| GDPR | Data encryption at rest |
| PCI-DSS | Payment data encryption |
| HIPAA | Health data protection |
