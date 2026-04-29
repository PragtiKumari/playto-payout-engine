import os
import random
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from payouts.models import Payout, LedgerEntry


from django.conf import settings


@shared_task
def process_pending_payouts():
    now = timezone.now()

    pending_payouts = Payout.objects.filter(
        status=Payout.PENDING
    ).filter(
        next_retry_at__isnull=True
    ) | Payout.objects.filter(
        status=Payout.PENDING,
        next_retry_at__lte=now
    )

    for payout in pending_payouts:
        if settings.USE_SYNC_TASKS:
            process_single_payout(str(payout.id))
        else:
            process_single_payout.delay(str(payout.id))

@shared_task
def process_single_payout(payout_id):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)

        if payout.status != Payout.PENDING:
            return f"Payout {payout_id} is not pending"

        payout.status = Payout.PROCESSING
        payout.processing_started_at = timezone.now()
        payout.attempts += 1
        payout.save()

    result = random.choices(
        ["success", "failure", "hang"],
        weights=[70, 20, 10],
        k=1,
    )[0]

    if result == "success":
        if settings.USE_SYNC_TASKS:
            mark_payout_completed(str(payout.id))
        else:
            mark_payout_completed.delay(str(payout.id))

    elif result == "failure":
        if settings.USE_SYNC_TASKS:
            mark_payout_failed(str(payout.id), "Bank settlement failed")
        else:
            mark_payout_failed.delay(str(payout.id), "Bank settlement failed")

    else:
        return f"Payout {payout_id} is stuck in processing"


@shared_task
def mark_payout_completed(payout_id):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)

        if not payout.can_transition_to(Payout.COMPLETED):
            return f"Illegal transition blocked for payout {payout_id}"

        payout.status = Payout.COMPLETED
        payout.save()

        return f"Payout {payout_id} completed"


@shared_task
def mark_payout_failed(payout_id, reason="Payout failed"):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)

        if not payout.can_transition_to(Payout.FAILED):
            return f"Illegal transition blocked for payout {payout_id}"

        payout.status = Payout.FAILED
        payout.failure_reason = reason
        payout.save()

        release_already_exists = LedgerEntry.objects.filter(
            merchant=payout.merchant,
            entry_type=LedgerEntry.PAYOUT_RELEASE,
            reference_id=str(payout.id),
        ).exists()

        if not release_already_exists:
            LedgerEntry.objects.create(
                merchant=payout.merchant,
                entry_type=LedgerEntry.PAYOUT_RELEASE,
                amount_paise=payout.amount_paise,
                description="Payout failed, held funds released",
                reference_id=str(payout.id),
            )

        return f"Payout {payout_id} failed and funds released"

@shared_task
def retry_stuck_processing_payouts():
    cutoff_time = timezone.now() - timedelta(seconds=30)

    stuck_payouts = Payout.objects.filter(
        status=Payout.PROCESSING,
        processing_started_at__lt=cutoff_time,
    )

    for payout in stuck_payouts:
        if payout.attempts >= 3:
            if settings.USE_SYNC_TASKS:
                mark_payout_failed(
                    str(payout.id),
                    "Max retry attempts reached",
                )
            else:
                mark_payout_failed.delay(
                    str(payout.id),
                    "Max retry attempts reached",
                )
        else:
            with transaction.atomic():
                locked_payout = Payout.objects.select_for_update().get(id=payout.id)

                if locked_payout.status == Payout.PROCESSING:
                    locked_payout.status = Payout.PENDING
                    locked_payout.next_retry_at = timezone.now() + timedelta(
                        seconds=2 ** locked_payout.attempts
                    )
                    locked_payout.save()

    return "Retry check completed"