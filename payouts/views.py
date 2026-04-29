from rest_framework.views import APIView
from rest_framework.response import Response

from payouts.models import Merchant, Payout, LedgerEntry
from payouts.serializers import (
    PayoutCreateSerializer,
    PayoutResponseSerializer,
    LedgerEntrySerializer,
)
from payouts.services import create_payout, get_merchant_balance


class CreatePayoutView(APIView):
    def post(self, request):
        merchant = Merchant.objects.first()

        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {"error": "Idempotency-Key header required"},
                status=400,
            )

        serializer = PayoutCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        response_data, status_code = create_payout(
            merchant,
            serializer.validated_data,
            idempotency_key,
        )

        return Response(response_data, status=status_code)


class DashboardView(APIView):
    def get(self, request):
        merchant = Merchant.objects.first()

        balance = get_merchant_balance(merchant)

        return Response({
            "available_balance": balance["available_balance"],
            "held_balance": balance["held_balance"],
        })


class PayoutListView(APIView):
    def get(self, request):
        merchant = Merchant.objects.first()

        payouts = Payout.objects.filter(merchant=merchant).order_by("-created_at")

        serializer = PayoutResponseSerializer(payouts, many=True)

        return Response(serializer.data)


class LedgerListView(APIView):
    def get(self, request):
        merchant = Merchant.objects.first()

        entries = LedgerEntry.objects.filter(merchant=merchant).order_by("-created_at")

        serializer = LedgerEntrySerializer(entries, many=True)

        return Response(serializer.data)