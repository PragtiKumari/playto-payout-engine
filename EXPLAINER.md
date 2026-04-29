# Playto Payout Engine – System Design Explanation

## Overview

This project simulates a payout system where merchants can transfer money to bank accounts. It is designed with production-grade concepts like idempotency, ledger-based accounting, retries, and async processing.

---

## Sample Flow

1. Merchant sends payout request with Idempotency-Key
2. System checks duplicate request
3. Ledger hold entry created
4. Payout marked pending
5. Background worker processes payout
6. Success → completed OR Failure → retry/release

---

## Why This Project Stands Out

- Handles idempotency like real payment systems
- Uses ledger instead of direct balance mutation
- Supports async processing and retries
- Prevents duplicate financial operations

---

## Key Design Decisions

### 1. Ledger-Based Accounting

Instead of storing balance directly, we store all transactions as ledger entries.

Types:
- credit → money added
- payout_hold → funds reserved
- payout_release → funds returned on failure

Balance is computed dynamically:
- available_balance = credits - holds + releases
- held_balance = active holds

Why?
- prevents inconsistency
- provides full audit trail
- matches real fintech systems

---

### 2. Idempotency Handling

Each payout request requires an Idempotency-Key.

We store:
- request hash
- response

Behavior:
- same key + same request → return same response
- same key + different request → reject (409 error)

Why?
- prevents duplicate payouts
- ensures safe retries

---

### 3. Async Processing with Celery

Payout processing is asynchronous.

Flow:
1. API creates payout → status = pending
2. Background worker picks it
3. Moves to processing
4. Simulates bank response
5. Marks completed or failed

Why?
- non-blocking API
- scalable design
- realistic architecture

---

### 4. Retry Mechanism

If payout fails:
- system retries with delay
- max attempts = 3
- after max attempts → mark failed

For stuck payouts:
- processing > 30 sec → retry triggered

---

### 5. Failure Handling

On failure:
- held funds are released
- duplicate release prevented

---

### 6. Data Consistency

All critical operations are:
- atomic
- idempotent-safe

---

## API Endpoints

### Create Payout
POST /api/v1/payouts

### Dashboard
GET /api/v1/dashboard

### Payout History
GET /api/v1/payouts/history

### Ledger
GET /api/v1/ledger

---

## Tech Stack

- Django + DRF
- SQLite (can be upgraded to Postgres)
- Celery (async processing)
- In-memory / filesystem broker (for local dev)

---

## Limitations

- No real bank integration (simulated)
- No authentication layer
- Basic retry logic

---

## Improvements (Future Scope)

- Add authentication (JWT)
- Use Redis for production Celery
- Add webhook system
- Add rate limiting
- Add monitoring & logging

---

## Conclusion

This system demonstrates how real-world payout engines are built using:

- idempotency
- ledger-based accounting
- async processing
- retry logic

It is designed to be scalable, safe, and production-aligned.