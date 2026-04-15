"""
Algorithm 105: Payment Ledger

- Transaction → ledger
- Ledger → replicated nodes
- Fast confirmation
- Immutable record
- Audit compliance
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class TransactionType(Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    TRANSFER = "transfer"
    REFUND = "refund"


class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERSED = "reversed"


@dataclass
class PaymentTransaction:
    """A payment transaction."""
    tx_id: str
    tx_type: TransactionType
    from_account: str
    to_account: str
    amount: float
    currency: str = "USD"
    status: TransactionStatus = TransactionStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class LedgerEntry:
    """An immutable ledger entry."""
    entry_id: int
    transaction: PaymentTransaction
    running_balance: float
    previous_hash: str
    entry_hash: str
    timestamp: float = field(default_factory=time.time)


class Account:
    """A financial account."""

    def __init__(self, account_id, initial_balance=0.0):
        self.account_id = account_id
        self.balance = initial_balance
        self.ledger_entries = []

    def credit(self, amount):
        self.balance += amount

    def debit(self, amount):
        if self.balance < amount:
            raise ValueError(f"Insufficient funds: {self.balance} < {amount}")
        self.balance -= amount


class PaymentLedger:
    """Immutable payment ledger with replication and audit compliance."""

    def __init__(self):
        self.entries = []
        self.accounts = {}
        self.tx_index = {}  # tx_id -> entry
        self.replicas = []

    def _compute_hash(self, entry_id, tx, prev_hash, balance):
        data = json.dumps({
            "entry_id": entry_id,
            "tx_id": tx.tx_id,
            "amount": tx.amount,
            "from": tx.from_account,
            "to": tx.to_account,
            "prev_hash": prev_hash,
            "balance": balance,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def create_account(self, account_id, initial_balance=0.0):
        account = Account(account_id, initial_balance)
        self.accounts[account_id] = account
        return account

    def process_transaction(self, transaction):
        """Process a payment transaction with confirmation."""
        # Validate
        if transaction.tx_type in (TransactionType.DEBIT, TransactionType.TRANSFER):
            from_acct = self.accounts.get(transaction.from_account)
            if not from_acct or from_acct.balance < transaction.amount:
                transaction.status = TransactionStatus.FAILED
                return transaction

        # Execute
        try:
            if transaction.tx_type == TransactionType.CREDIT:
                to_acct = self.accounts.get(transaction.to_account)
                if to_acct:
                    to_acct.credit(transaction.amount)

            elif transaction.tx_type == TransactionType.DEBIT:
                from_acct = self.accounts[transaction.from_account]
                from_acct.debit(transaction.amount)

            elif transaction.tx_type == TransactionType.TRANSFER:
                from_acct = self.accounts[transaction.from_account]
                to_acct = self.accounts.get(transaction.to_account)
                from_acct.debit(transaction.amount)
                if to_acct:
                    to_acct.credit(transaction.amount)

            elif transaction.tx_type == TransactionType.REFUND:
                to_acct = self.accounts.get(transaction.to_account)
                if to_acct:
                    to_acct.credit(transaction.amount)

            transaction.status = TransactionStatus.CONFIRMED
        except ValueError:
            transaction.status = TransactionStatus.FAILED
            return transaction

        # Record in ledger
        self._append_entry(transaction)

        # Replicate
        for replica in self.replicas:
            replica._append_entry(transaction)

        return transaction

    def _append_entry(self, transaction):
        """Append an immutable entry to the ledger."""
        entry_id = len(self.entries)
        prev_hash = self.entries[-1].entry_hash if self.entries else "0" * 64

        to_acct = self.accounts.get(transaction.to_account)
        balance = to_acct.balance if to_acct else 0

        entry_hash = self._compute_hash(entry_id, transaction, prev_hash, balance)

        entry = LedgerEntry(
            entry_id=entry_id,
            transaction=transaction,
            running_balance=balance,
            previous_hash=prev_hash,
            entry_hash=entry_hash,
        )

        self.entries.append(entry)
        self.tx_index[transaction.tx_id] = entry

    def get_transaction(self, tx_id):
        """Get transaction by ID."""
        entry = self.tx_index.get(tx_id)
        return entry.transaction if entry else None

    def get_account_history(self, account_id):
        """Get transaction history for an account."""
        return [
            entry for entry in self.entries
            if entry.transaction.from_account == account_id
            or entry.transaction.to_account == account_id
        ]

    def verify_integrity(self):
        """Verify ledger integrity."""
        for i in range(1, len(self.entries)):
            if self.entries[i].previous_hash != self.entries[i - 1].entry_hash:
                return False, f"Chain broken at entry {i}"
        return True, "Ledger integrity verified"

    def generate_audit_report(self, account_id=None):
        """Generate audit compliance report."""
        entries = self.get_account_history(account_id) if account_id else self.entries

        total_credits = sum(
            e.transaction.amount for e in entries
            if e.transaction.tx_type in (TransactionType.CREDIT, TransactionType.REFUND)
        )
        total_debits = sum(
            e.transaction.amount for e in entries
            if e.transaction.tx_type == TransactionType.DEBIT
        )

        return {
            "total_entries": len(entries),
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_flow": total_credits - total_debits,
            "integrity": self.verify_integrity()[0],
            "generated_at": time.time(),
        }


if __name__ == "__main__":
    ledger = PaymentLedger()

    # Create accounts
    ledger.create_account("acct-alice", 1000.0)
    ledger.create_account("acct-bob", 500.0)
    ledger.create_account("acct-charlie", 200.0)

    # Process transactions
    transactions = [
        PaymentTransaction("tx1", TransactionType.TRANSFER, "acct-alice", "acct-bob", 100.0),
        PaymentTransaction("tx2", TransactionType.TRANSFER, "acct-bob", "acct-charlie", 50.0),
        PaymentTransaction("tx3", TransactionType.CREDIT, "", "acct-alice", 200.0),
        PaymentTransaction("tx4", TransactionType.DEBIT, "acct-charlie", "", 30.0),
    ]

    for tx in transactions:
        result = ledger.process_transaction(tx)
        print(f"{result.tx_id}: {result.status.value} "
              f"({result.from_account or 'ext'} → {result.to_account or 'ext'}: ${result.amount})")

    # Balances
    print("\nBalances:")
    for acct_id, acct in ledger.accounts.items():
        print(f"  {acct_id}: ${acct.balance:.2f}")

    # Audit
    valid, msg = ledger.verify_integrity()
    print(f"\n{msg}")

    report = ledger.generate_audit_report()
    print(f"Audit: {report['total_entries']} entries, net=${report['net_flow']:.2f}")
