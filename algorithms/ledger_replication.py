"""
Algorithm 99: Ledger Replication

- Transaction → ledger node
- Node → consensus protocol
- Fast replication
- Immutable record
- Audit trail
"""

import time
import hashlib
import json
from dataclasses import dataclass, field


@dataclass
class Transaction:
    """An immutable ledger transaction."""
    tx_id: str
    sender: str
    receiver: str
    amount: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class LedgerEntry:
    """An immutable ledger entry with chain linking."""
    index: int
    transaction: Transaction
    previous_hash: str
    hash: str
    timestamp: float = field(default_factory=time.time)
    node_id: str = ""


class LedgerNode:
    """A node maintaining a replicated ledger."""

    def __init__(self, node_id):
        self.node_id = node_id
        self.chain = []
        self.pending = []

    def _compute_hash(self, index, tx, prev_hash, timestamp):
        data = json.dumps({
            "index": index,
            "tx_id": tx.tx_id,
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def append(self, transaction):
        """Append a transaction to the ledger."""
        index = len(self.chain)
        prev_hash = self.chain[-1].hash if self.chain else "0" * 64
        timestamp = time.time()

        entry_hash = self._compute_hash(index, transaction, prev_hash, timestamp)

        entry = LedgerEntry(
            index=index,
            transaction=transaction,
            previous_hash=prev_hash,
            hash=entry_hash,
            timestamp=timestamp,
            node_id=self.node_id,
        )
        self.chain.append(entry)
        return entry

    def verify_integrity(self):
        """Verify the integrity of the entire ledger chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.previous_hash != previous.hash:
                return False, f"Chain broken at index {i}"

            expected_hash = self._compute_hash(
                current.index, current.transaction,
                current.previous_hash, current.timestamp,
            )
            if current.hash != expected_hash:
                return False, f"Hash mismatch at index {i}"

        return True, "Ledger integrity verified"

    def get_audit_trail(self, entity=None):
        """Get audit trail for an entity (sender or receiver)."""
        if entity is None:
            return self.chain

        return [
            entry for entry in self.chain
            if entry.transaction.sender == entity
            or entry.transaction.receiver == entity
        ]

    @property
    def length(self):
        return len(self.chain)


class ConsensusManager:
    """Simple consensus for ledger replication."""

    def __init__(self, nodes):
        self.nodes = nodes

    def propose(self, transaction):
        """Propose a transaction via consensus."""
        votes = 0
        for node in self.nodes:
            if self._validate_transaction(transaction):
                votes += 1

        majority = len(self.nodes) // 2 + 1
        return votes >= majority

    @staticmethod
    def _validate_transaction(tx):
        """Validate a transaction."""
        if tx.amount <= 0:
            return False
        if not tx.sender or not tx.receiver:
            return False
        if tx.sender == tx.receiver:
            return False
        return True


class ReplicatedLedger:
    """Replicated ledger with consensus and audit trail."""

    def __init__(self, num_nodes=3):
        self.nodes = [LedgerNode(f"node-{i}") for i in range(num_nodes)]
        self.consensus = ConsensusManager(self.nodes)
        self.transaction_log = []

    def submit_transaction(self, transaction):
        """Submit a transaction with consensus-based replication."""
        if not self.consensus.propose(transaction):
            return None

        entries = []
        for node in self.nodes:
            entry = node.append(transaction)
            entries.append(entry)

        self.transaction_log.append(transaction)
        return entries[0] if entries else None

    def verify_all(self):
        """Verify integrity across all nodes."""
        results = {}
        for node in self.nodes:
            valid, message = node.verify_integrity()
            results[node.node_id] = {"valid": valid, "message": message}
        return results

    def check_consistency(self):
        """Check consistency across all nodes."""
        if not self.nodes:
            return True

        reference = self.nodes[0]
        for node in self.nodes[1:]:
            if node.length != reference.length:
                return False
            for i in range(node.length):
                if node.chain[i].hash != reference.chain[i].hash:
                    return False
        return True

    def get_audit_trail(self, entity=None):
        """Get audit trail from the primary node."""
        if self.nodes:
            return self.nodes[0].get_audit_trail(entity)
        return []

    def get_balance(self, entity):
        """Calculate balance for an entity."""
        balance = 0.0
        for entry in self.nodes[0].chain:
            tx = entry.transaction
            if tx.receiver == entity:
                balance += tx.amount
            if tx.sender == entity:
                balance -= tx.amount
        return balance


if __name__ == "__main__":
    ledger = ReplicatedLedger(num_nodes=3)

    transactions = [
        Transaction("tx1", "Alice", "Bob", 100.0),
        Transaction("tx2", "Bob", "Charlie", 50.0),
        Transaction("tx3", "Charlie", "Alice", 25.0),
        Transaction("tx4", "Alice", "Bob", 30.0),
    ]

    for tx in transactions:
        entry = ledger.submit_transaction(tx)
        if entry:
            print(f"Committed: {tx.tx_id} ({tx.sender} → {tx.receiver}: ${tx.amount})")

    # Verify integrity
    verification = ledger.verify_all()
    for node_id, result in verification.items():
        print(f"\n{node_id}: {result['message']}")

    print(f"\nConsistent: {ledger.check_consistency()}")

    # Audit trail
    print(f"\nAlice's audit trail:")
    for entry in ledger.get_audit_trail("Alice"):
        tx = entry.transaction
        print(f"  {tx.tx_id}: {tx.sender} → {tx.receiver}: ${tx.amount}")

    # Balances
    for entity in ["Alice", "Bob", "Charlie"]:
        print(f"{entity} balance: ${ledger.get_balance(entity):.2f}")
