from django.db.models import Sum
from django.db.models.functions import Coalesce

from payouts.models import LedgerEntry


def get_merchant_balance(merchant):
    """
    Returns:
    {
        "available_balance": int,
        "held_balance": int
    }
    """

    # Total credits
    total_credits = (
        LedgerEntry.objects.filter(
            merchant=merchant,
            entry_type=LedgerEntry.CREDIT
        )
        .aggregate(total=Coalesce(Sum("amount_paise"), 0))["total"]
    )

    # Total holds (pending payouts)
    total_holds = (
        LedgerEntry.objects.filter(
            merchant=merchant,
            entry_type=LedgerEntry.PAYOUT_HOLD
        )
        .aggregate(total=Coalesce(Sum("amount_paise"), 0))["total"]
    )

    # Total releases (failed payout returns)
    total_releases = (
        LedgerEntry.objects.filter(
            merchant=merchant,
            entry_type=LedgerEntry.PAYOUT_RELEASE
        )
        .aggregate(total=Coalesce(Sum("amount_paise"), 0))["total"]
    )

    available_balance = total_credits + total_releases - total_holds
    held_balance = total_holds

    return {
        "available_balance": available_balance,
        "held_balance": held_balance,
    }




import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from payouts.models import (
    Payout,
    LedgerEntry,
    BankAccount,
    IdempotencyKey,
)


def create_payout(merchant, data, idempotency_key):
    amount = data["amount_paise"]
    bank_account_id = data["bank_account_id"]

    request_hash = hashlib.sha256(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

    now = timezone.now()

    # Check existing idempotency key
    existing = IdempotencyKey.objects.filter(
        merchant=merchant,
        key=idempotency_key
    ).first()

    if existing:
        if existing.request_hash != request_hash:
            return {
                "error": "Idempotency key resused with different request body"
            }, 409
        if existing.response_body:
            return existing.response_body, existing.status_code
        
        return {"error": "Request is already being processed"}, 409
        
    with transaction.atomic():

        # Lock merchant row (critical for concurrency)
        merchant_locked = (
            type(merchant)
            .objects.select_for_update()
            .get(id=merchant.id)
        )

        from payouts.services import get_merchant_balance
        balance = get_merchant_balance(merchant_locked)

        if balance["available_balance"] < amount:
            return {"error": "Insufficient balance"}, 400

        # Create idempotency record
        idempotency = IdempotencyKey.objects.create(
            merchant=merchant_locked,
            key=idempotency_key,
            request_hash=request_hash,
            locked_until=now + timedelta(seconds=30),
            expires_at=now + timedelta(hours=24),
        )

        # Validate bank account
        try:
            bank_account = BankAccount.objects.get(
                id=bank_account_id,
                merchant=merchant_locked,
                is_active=True,
            )
        except BankAccount.DoesNotExist:
            return {"error": "Invalid bank account"}, 400

        # Create payout
        payout = Payout.objects.create(
            merchant=merchant_locked,
            bank_account=bank_account,
            amount_paise=amount,
            status=Payout.PENDING,
        )

        # Create ledger HOLD entry
        LedgerEntry.objects.create(
            merchant=merchant_locked,
            entry_type=LedgerEntry.PAYOUT_HOLD,
            amount_paise=amount,
            description="Payout hold",
            reference_id=str(payout.id),
        )

        response_data = {
            "id": str(payout.id),
            "amount_paise": payout.amount_paise,
            "status": payout.status,
        }

        # Save response for idempotency
        idempotency.response_body = response_data
        idempotency.status_code = 201
        idempotency.save()

        return response_data, 201