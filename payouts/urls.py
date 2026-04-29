from django.urls import path
from payouts.views import (
    CreatePayoutView,
    DashboardView,
    PayoutListView,
    LedgerListView,
)

urlpatterns = [
    path("dashboard", DashboardView.as_view()),
    path("payouts", CreatePayoutView.as_view()),
    path("payouts/history", PayoutListView.as_view()),
    path("ledger", LedgerListView.as_view()),
]