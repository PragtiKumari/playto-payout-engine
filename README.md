# Playto Payout Engine

A backend system that simulates a real-world payout engine used in fintech platforms. It handles merchant balances, payout requests, ledger tracking, idempotency, and failure-safe processing.

---

## Live Demo

Base URL:  
https://playto-payout-engine-ubsb.onrender.com

Key endpoints:
- /api/v1/dashboard
- /api/v1/payouts/history
- /api/v1/ledger

Note: First request may take a few seconds as the free instance spins up.

---

## Features

- Idempotent payout creation to prevent duplicate payouts  
- Ledger-based accounting system (no direct balance storage)  
- Payout hold and release mechanism  
- Failure-safe refund handling  
- Async-compatible architecture using Celery  
- Clean REST APIs  
- Live deployed backend with seeded test data  

---

## How it works

Instead of storing balance directly, the system uses a ledger.

- credit → adds money  
- payout_hold → reserves money  
- payout_release → refunds on failure  

Balance is calculated dynamically:

available_balance = credits - holds + releases  
held_balance = active holds  

---

## Idempotency

Each payout request requires an Idempotency-Key.

- Same request + same key → same response  
- Same key + different request → rejected  

This ensures no duplicate payouts or double deduction of funds.

---

## Payout Flow

1. Request received  
2. Idempotency validated  
3. Balance checked  
4. Funds moved to hold  
5. Payout created  
6. Processed (async-compatible)  
7. Completed or failed  

If failed, funds are safely returned using the ledger.

---

## API Example

POST /api/v1/payouts

Headers:
Idempotency-Key: <UUID>

Body:
{
  "amount_paise": 50000,
  "bank_account_id": 1
}

---

## Tech Stack

- Django  
- Django REST Framework  
- Celery  
- SQLite  
- Gunicorn  
- Render  

---

## Deployment

- Hosted on Render  
- Auto migrations and seed data on startup  
- Sync fallback used for Celery due to free tier limitations  

---

## Notes

- Designed to simulate real payout systems  
- Can be scaled using PostgreSQL and Redis  
- Focused on correctness and system design  

---

## Author

Pragti Kumari
