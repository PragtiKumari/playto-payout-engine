from django.core.management.base import BaseCommand
from payouts.models import Merchant, BankAccount, LedgerEntry


class Command(BaseCommand):
    help = "Seed initial merchants, bank accounts, and credit ledger entries"

    def handle(self, *args, **kwargs):
        merchants_data = [
            {
                "name": "Aarav Digital Studio",
                "email": "aarav@example.com",
                "bank_name": "HDFC Bank",
                "account_holder_name": "Aarav Digital Studio",
                "account_number_last4": "1234",
                "ifsc_code": "HDFC0001234",
                "credits": [500000, 300000, 200000],
            },
            {
                "name": "Meera Design Agency",
                "email": "meera@example.com",
                "bank_name": "ICICI Bank",
                "account_holder_name": "Meera Design Agency",
                "account_number_last4": "5678",
                "ifsc_code": "ICIC0005678",
                "credits": [1000000, 450000, 250000],
            },
            {
                "name": "Kabir Freelance Works",
                "email": "kabir@example.com",
                "bank_name": "SBI Bank",
                "account_holder_name": "Kabir Freelance Works",
                "account_number_last4": "9012",
                "ifsc_code": "SBIN0009012",
                "credits": [700000, 150000],
            },
        ]

        for data in merchants_data:
            merchant, _ = Merchant.objects.get_or_create(
                email=data["email"],
                defaults={"name": data["name"]},
            )

            BankAccount.objects.get_or_create(
                merchant=merchant,
                account_number_last4=data["account_number_last4"],
                defaults={
                    "account_holder_name": data["account_holder_name"],
                    "bank_name": data["bank_name"],
                    "ifsc_code": data["ifsc_code"],
                    "is_active": True,
                },
            )

            if not LedgerEntry.objects.filter(
                merchant=merchant,
                entry_type=LedgerEntry.CREDIT,
                description__startswith="Seed credit",
            ).exists():
                for amount in data["credits"]:
                    LedgerEntry.objects.create(
                        merchant=merchant,
                        entry_type=LedgerEntry.CREDIT,
                        amount_paise=amount,
                        description=f"Seed credit of {amount} paise",
                        reference_id=f"seed-{merchant.id}-{amount}",
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Seeded merchant: {merchant.name}")
            )

        self.stdout.write(self.style.SUCCESS("Seed data completed successfully"))