"""
Algorithm 100: Identity Hashing

- User ID → hash function
- Fast lookup
- Secure storage
- Collision-free
- Privacy preserved
"""

import hashlib
import secrets
import time
from dataclasses import dataclass, field


@dataclass
class HashedIdentity:
    """A hashed user identity."""
    original_id: str  # Only stored during creation, not persisted
    hashed_id: str
    salt: str
    algorithm: str
    created_at: float = field(default_factory=time.time)


class IdentityHasher:
    """Secure identity hashing with collision avoidance."""

    def __init__(self, algorithm="sha256", salt_length=32, pepper=""):
        self.algorithm = algorithm
        self.salt_length = salt_length
        self.pepper = pepper
        self.hash_store = {}  # hashed_id -> metadata
        self.lookup_table = {}  # hashed_id -> salt (for verification)
        self._collision_count = 0

    def hash_identity(self, user_id):
        """Hash a user ID with salt for secure storage."""
        salt = secrets.token_hex(self.salt_length)
        hashed = self._compute_hash(user_id, salt)

        # Collision check
        if hashed in self.hash_store:
            self._collision_count += 1
            salt = secrets.token_hex(self.salt_length)
            hashed = self._compute_hash(user_id, salt)

        identity = HashedIdentity(
            original_id=user_id,
            hashed_id=hashed,
            salt=salt,
            algorithm=self.algorithm,
        )

        self.hash_store[hashed] = {
            "salt": salt,
            "algorithm": self.algorithm,
            "created_at": identity.created_at,
        }
        self.lookup_table[hashed] = salt

        return identity

    def _compute_hash(self, user_id, salt):
        """Compute hash with salt and pepper."""
        data = f"{salt}{user_id}{self.pepper}"
        if self.algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        elif self.algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        elif self.algorithm == "blake2b":
            return hashlib.blake2b(data.encode()).hexdigest()
        else:
            return hashlib.sha256(data.encode()).hexdigest()

    def verify(self, user_id, hashed_id):
        """Verify a user ID against a stored hash."""
        metadata = self.hash_store.get(hashed_id)
        if metadata is None:
            return False

        computed = self._compute_hash(user_id, metadata["salt"])
        return secrets.compare_digest(computed, hashed_id)

    def lookup(self, hashed_id):
        """Fast lookup to check if a hashed ID exists."""
        return hashed_id in self.hash_store

    def get_stats(self):
        """Get hashing statistics."""
        return {
            "total_identities": len(self.hash_store),
            "collisions": self._collision_count,
            "algorithm": self.algorithm,
        }


class PrivacyPreservingStore:
    """Store user data with privacy-preserving hashed identities."""

    def __init__(self, algorithm="sha256"):
        self.hasher = IdentityHasher(algorithm=algorithm, pepper=secrets.token_hex(16))
        self.user_data = {}  # hashed_id -> encrypted data
        self.id_mapping = {}  # For demo: user_id -> hashed_id

    def register_user(self, user_id, data=None):
        """Register a user with hashed identity."""
        identity = self.hasher.hash_identity(user_id)
        self.user_data[identity.hashed_id] = data or {}
        self.id_mapping[user_id] = identity.hashed_id
        return identity.hashed_id

    def get_user_data(self, user_id):
        """Get user data using original ID (verified)."""
        hashed_id = self.id_mapping.get(user_id)
        if hashed_id is None:
            return None

        if self.hasher.verify(user_id, hashed_id):
            return self.user_data.get(hashed_id)
        return None

    def update_user_data(self, user_id, data):
        """Update user data."""
        hashed_id = self.id_mapping.get(user_id)
        if hashed_id and self.hasher.verify(user_id, hashed_id):
            self.user_data[hashed_id] = data
            return True
        return False

    def delete_user(self, user_id):
        """Delete user data (right to be forgotten)."""
        hashed_id = self.id_mapping.get(user_id)
        if hashed_id:
            self.user_data.pop(hashed_id, None)
            del self.id_mapping[user_id]
            return True
        return False


if __name__ == "__main__":
    # Basic hashing
    hasher = IdentityHasher(algorithm="sha256")

    users = ["alice@example.com", "bob@example.com", "charlie@example.com"]
    for user_id in users:
        identity = hasher.hash_identity(user_id)
        print(f"User: {user_id}")
        print(f"  Hash: {identity.hashed_id[:40]}...")
        print(f"  Verified: {hasher.verify(user_id, identity.hashed_id)}")

    print(f"\nStats: {hasher.get_stats()}")

    # Privacy-preserving store
    store = PrivacyPreservingStore()

    hashed = store.register_user("alice@example.com", {"name": "Alice", "role": "admin"})
    print(f"\nRegistered Alice: {hashed[:40]}...")

    data = store.get_user_data("alice@example.com")
    print(f"Retrieved: {data}")

    store.update_user_data("alice@example.com", {"name": "Alice", "role": "user"})
    print(f"Updated: {store.get_user_data('alice@example.com')}")

    store.delete_user("alice@example.com")
    print(f"Deleted: {store.get_user_data('alice@example.com')}")
