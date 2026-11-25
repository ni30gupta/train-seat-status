from django.urls import path
from monitor.views import status, check_now

urlpatterns = [
    path("api/status/", status, name="status"),
    path("api/check-now/", check_now, name="check-now"),
]
