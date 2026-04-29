from rest_framework import serializers
from payouts.models import Payout, LedgerEntry


class PayoutCreateSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.IntegerField()


class PayoutResponseSerializer(serializers.ModelSerializer):
    bank_account = serializers.SerializerMethodField()

    class Meta:
        model = Payout
        fields = [
            "id",
            "amount_paise",
            "status",
            "attempts",
            "bank_account",
            "failure_reason",
            "created_at",
            "updated_at",
        ]

    def get_bank_account(self, obj):
        return {
            "id": obj.bank_account.id,
            "bank_name": obj.bank_account.bank_name,
            "account_number_last4": obj.bank_account.account_number_last4,
        }


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "entry_type",
            "amount_paise",
            "description",
            "reference_id",
            "created_at",
        ]