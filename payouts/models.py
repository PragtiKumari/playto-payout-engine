import uuid
from django.db import models
from django.utils import timezone


class Merchant(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="bank_accounts"
    )
    account_holder_name = models.CharField(max_length=120)
    bank_name = models.CharField(max_length=120)
    account_number_last4 = models.CharField(max_length=4)
    ifsc_code = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} ****{self.account_number_last4}"


class LedgerEntry(models.Model):
    CREDIT = "credit"
    PAYOUT_HOLD = "payout_hold"
    PAYOUT_RELEASE = "payout_release"

    ENTRY_TYPE_CHOICES = [
        (CREDIT, "Credit"),
        (PAYOUT_HOLD, "Payout Hold"),
        (PAYOUT_RELEASE, "Payout Release"),
    ]

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="ledger_entries"
    )
    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPE_CHOICES)
    amount_paise = models.BigIntegerField()
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.merchant.name} | {self.entry_type} | {self.amount_paise}"


class Payout(models.Model):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="payouts"
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="payouts"
    )

    amount_paise = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    attempts = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)

    failure_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_transition_to(self, new_status):
        allowed_transitions = {
            self.PENDING: [self.PROCESSING],
            self.PROCESSING: [self.COMPLETED, self.FAILED],
            self.COMPLETED: [],
            self.FAILED: [],
        }

        return new_status in allowed_transitions[self.status]

    def __str__(self):
        return f"{self.id} | {self.merchant.name} | {self.status}"


class IdempotencyKey(models.Model):
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="idempotency_keys"
    )

    key = models.UUIDField()
    request_hash = models.CharField(max_length=64)
    response_body = models.JSONField(null=True, blank=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)

    locked_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("merchant", "key")

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.merchant.name} | {self.key}"