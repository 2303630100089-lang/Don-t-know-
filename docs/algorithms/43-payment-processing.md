# 43. Algorithm: Payment Processing

## Overview

Secure, reliable payment processing pipeline from user initiation through gateway processing, bank confirmation, ledger updates, and merchant/user notifications.

## Algorithm Steps

### Step 1: User Initiates → Gateway
- User submits payment request with amount, currency, payment method.
- Client-side validation (card number format, expiry, CVV).
- Request encrypted with TLS and sent to payment gateway.
- Gateway generates unique transaction ID.
- Idempotency key prevents duplicate charges.

### Step 2: Gateway → Bank API
- Gateway tokenizes sensitive card data (PCI-DSS compliance).
- Sends authorization request to acquiring bank.
- Acquiring bank routes to card network (Visa/Mastercard).
- Card network forwards to issuing bank.
- 3D Secure challenge if required.

### Step 3: Bank API → Confirmation
- Issuing bank validates: sufficient funds, fraud checks, account status.
- Authorization response: Approved / Declined / Pending.
- Authorization code generated for approved transactions.
- Hold placed on cardholder's funds.
- Response propagated back through the chain.

### Step 4: Confirmation → Ledger Update
- Transaction recorded in distributed ledger.
- Double-entry bookkeeping: debit + credit entries.
- Ledger replicated across data centers for durability.
- Settlement batch prepared for end-of-day processing.
- Audit trail with complete transaction history.

### Step 5: Ledger → User + Merchant Notification
- User receives confirmation (push notification + in-app + email).
- Merchant receives settlement notification.
- Transaction status updated in user's transaction history.
- Receipt generated and stored.
- Analytics events emitted for reporting.

## Pseudocode

```
function processPayment(user, amount, payment_method):
    // Step 1: Initiate
    txn_id = generateTransactionId()
    validateIdempotencyKey(user.idempotency_key)
    
    // Step 2: Gateway → Bank
    token = tokenize(payment_method)
    auth_request = {
        txn_id, token, amount, currency,
        merchant_id, timestamp
    }
    
    // Step 3: Bank Confirmation
    auth_response = bankAPI.authorize(auth_request)
    
    if auth_response.status == DECLINED:
        notifyUser(user, PAYMENT_DECLINED, auth_response.reason)
        return DECLINED
    
    // Step 4: Ledger Update
    ledger.record({
        txn_id,
        debit: { account: user.account, amount },
        credit: { account: merchant.account, amount },
        auth_code: auth_response.auth_code,
        timestamp: now()
    })
    
    // Step 5: Notifications
    parallel:
        notifyUser(user, PAYMENT_SUCCESS, txn_id)
        notifyMerchant(merchant, PAYMENT_RECEIVED, txn_id)
        emitAnalyticsEvent(PAYMENT_COMPLETED, txn_id)
    
    return SUCCESS

function handleFailure(txn_id, error):
    if error.type == TIMEOUT:
        retryWithBackoff(txn_id)
    elif error.type == NETWORK:
        queryTransactionStatus(txn_id)  // Check if already processed
    else:
        rollback(txn_id)
        notifyUser(user, PAYMENT_FAILED, error)
```

## Flow Diagram

```
User ──▶ Gateway ──▶ Bank API ──▶ Confirmation
                                       │
                                       ▼
                              ┌──────────────┐
                              │   Ledger     │
                              │   Update     │
                              └──────┬───────┘
                                     │
                           ┌─────────┼─────────┐
                           ▼                   ▼
                     User Notified      Merchant Notified
```

## Performance Targets

| Metric | Target |
|--------|--------|
| End-to-end latency | < 2 seconds |
| Authorization | < 500ms |
| Ledger write | < 50ms |
| Notification | < 1 second |
| Success rate | > 99.5% |
