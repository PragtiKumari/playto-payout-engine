from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("payouts.urls")),
]

from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "Payout Engine API is live",
        "endpoints": [
            "/api/v1/dashboard",
            "/api/v1/payouts/history",
            "/api/v1/ledger"
        ]
    })



from django.urls import path, include

urlpatterns = [
    path('', home),   # 👈 ADD THIS
    path('admin/', admin.site.urls),
    path('api/v1/', include('payouts.urls')),
]

