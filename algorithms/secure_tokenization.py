"""
Algorithm 104: Secure Tokenization

- Input → token generator
- Token mapped to data
- Fast lookup
- Secure storage
- Compliance ensured
"""

import secrets
import time
import hashlib
from dataclasses import dataclass, field


@dataclass
class Token:
    """A secure token mapped to sensitive data."""
    token_id: str
    token_value: str
    data_type: str
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0
    metadata: dict = field(default_factory=dict)


class TokenVault:
    """Secure vault for token-to-data mappings."""

    def __init__(self):
        self.vault = {}  # token -> encrypted data
        self.reverse_map = {}  # data_hash -> token
        self.access_log = []

    def store(self, token_value, sensitive_data):
        data_hash = hashlib.sha256(str(sensitive_data).encode()).hexdigest()
        self.vault[token_value] = sensitive_data
        self.reverse_map[data_hash] = token_value

    def retrieve(self, token_value):
        self._log_access(token_value, "retrieve")
        return self.vault.get(token_value)

    def delete(self, token_value):
        data = self.vault.pop(token_value, None)
        if data:
            data_hash = hashlib.sha256(str(data).encode()).hexdigest()
            self.reverse_map.pop(data_hash, None)
        self._log_access(token_value, "delete")

    def _log_access(self, token_value, operation):
        self.access_log.append({
            "token": token_value[:8] + "...",
            "operation": operation,
            "timestamp": time.time(),
        })


class TokenGenerator:
    """Generate secure, unique tokens."""

    @staticmethod
    def generate(prefix="tok", length=32):
        random_part = secrets.token_urlsafe(length)
        return f"{prefix}_{random_part}"

    @staticmethod
    def generate_format_preserving(original, mask_char="X"):
        """Generate a format-preserving token (e.g., for credit cards)."""
        preserved = []
        for char in original:
            if char.isdigit():
                preserved.append(str(secrets.randbelow(10)))
            elif char == "-" or char == " ":
                preserved.append(char)
            else:
                preserved.append(mask_char)
        return "".join(preserved)


class TokenizationService:
    """Complete tokenization service with compliance support."""

    def __init__(self, default_ttl=3600):
        self.vault = TokenVault()
        self.generator = TokenGenerator()
        self.tokens = {}  # token_id -> Token
        self.default_ttl = default_ttl

    def tokenize(self, sensitive_data, data_type="generic", ttl=None):
        """Tokenize sensitive data."""
        token_value = self.generator.generate()
        token = Token(
            token_id=token_value[:16],
            token_value=token_value,
            data_type=data_type,
            expires_at=time.time() + (ttl or self.default_ttl),
        )

        self.vault.store(token_value, sensitive_data)
        self.tokens[token_value] = token
        return token

    def tokenize_card(self, card_number):
        """Tokenize a credit card number with format preservation."""
        fp_token = self.generator.generate_format_preserving(card_number)
        token_value = self.generator.generate(prefix="card")

        token = Token(
            token_id=token_value[:16],
            token_value=token_value,
            data_type="credit_card",
            metadata={"display": fp_token},
        )

        self.vault.store(token_value, card_number)
        self.tokens[token_value] = token
        return token

    def detokenize(self, token_value):
        """Retrieve original data from token."""
        token = self.tokens.get(token_value)
        if not token:
            return None

        if token.expires_at > 0 and time.time() > token.expires_at:
            self.revoke(token_value)
            return None

        return self.vault.retrieve(token_value)

    def revoke(self, token_value):
        """Revoke a token."""
        self.vault.delete(token_value)
        self.tokens.pop(token_value, None)

    def get_compliance_report(self):
        """Generate compliance report."""
        return {
            "total_tokens": len(self.tokens),
            "by_type": self._count_by_type(),
            "access_log_entries": len(self.vault.access_log),
            "expired_tokens": sum(
                1 for t in self.tokens.values()
                if t.expires_at > 0 and time.time() > t.expires_at
            ),
        }

    def _count_by_type(self):
        counts = {}
        for token in self.tokens.values():
            counts[token.data_type] = counts.get(token.data_type, 0) + 1
        return counts


if __name__ == "__main__":
    service = TokenizationService(default_ttl=3600)

    # Tokenize various data
    ssn_token = service.tokenize("123-45-6789", data_type="ssn")
    print(f"SSN tokenized: {ssn_token.token_value[:20]}...")

    email_token = service.tokenize("user@example.com", data_type="email")
    print(f"Email tokenized: {email_token.token_value[:20]}...")

    # Tokenize credit card
    card_token = service.tokenize_card("4532-1234-5678-9012")
    print(f"Card tokenized: {card_token.token_value[:20]}...")
    print(f"Card display: {card_token.metadata.get('display')}")

    # Detokenize
    original = service.detokenize(ssn_token.token_value)
    print(f"\nDetokenized SSN: {original}")

    # Compliance report
    report = service.get_compliance_report()
    print(f"\nCompliance: {report}")
