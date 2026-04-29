from django.contrib import admin
from .models import Merchant, BankAccount, LedgerEntry, Payout, IdempotencyKey


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "created_at")
    search_fields = ("name", "email")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "merchant",
        "account_holder_name",
        "bank_name",
        "account_number_last4",
        "ifsc_code",
        "is_active",
    )
    list_filter = ("is_active", "bank_name")
    search_fields = ("merchant__name", "account_holder_name", "bank_name")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "merchant",
        "entry_type",
        "amount_paise",
        "reference_id",
        "created_at",
    )
    list_filter = ("entry_type",)
    search_fields = ("merchant__name", "reference_id")


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "merchant",
        "bank_account",
        "amount_paise",
        "status",
        "attempts",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("merchant__name", "id")


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "merchant",
        "key",
        "status_code",
        "expires_at",
        "created_at",
    )
    search_fields = ("merchant__name", "key")