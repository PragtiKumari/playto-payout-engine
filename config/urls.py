from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from payouts.models import Merchant, Payout, LedgerEntry
from payouts.services import get_merchant_balance


def home(request):
    merchant = Merchant.objects.first()

    if not merchant:
        return JsonResponse({
            "message": "Payout Engine API is live",
            "status": "no seed data found",
            "next_step": "Run migrations and seed_data command"
        })

    balance = get_merchant_balance(merchant)

    return JsonResponse({
        "message": "Playto Payout Engine API is live",
        "status": "healthy",
        "merchant": {
            "id": merchant.id,
            "name": merchant.name,
            "email": merchant.email,
        },
        "live_balance": {
            "available_balance_paise": balance["available_balance"],
            "held_balance_paise": balance["held_balance"],
        },
        "live_counts": {
            "total_payouts": Payout.objects.filter(merchant=merchant).count(),
            "total_ledger_entries": LedgerEntry.objects.filter(merchant=merchant).count(),
        },
        "features_implemented": [
            "Merchant ledger with paise based accounting",
            "Idempotent payout request API",
            "Payout hold and release logic",
            "Background worker compatible payout processing",
            "Failed payout refund handling",
            "Payout history and ledger APIs"
        ],
        "test_endpoints": {
            "dashboard": "/api/v1/dashboard",
            "payout_history": "/api/v1/payouts/history",
            "ledger": "/api/v1/ledger",
            "create_payout": {
                "method": "POST",
                "url": "/api/v1/payouts",
                "headers": {
                    "Idempotency-Key": "valid UUID required",
                    "Content-Type": "application/json"
                },
                "sample_body": {
                    "amount_paise": 50000,
                    "bank_account_id": 1
                }
            }
        },
        "note": "Seeded with test data. Free Render instance may take a few seconds to wake up."
    })


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/v1/", include("payouts.urls")),
]