import os
from datetime import date
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import SeatState
from .tasks import check_seat_availability

@require_GET
def status(request):
    state = SeatState.objects.first()
    if state is None:
        return JsonResponse({
            "configured": True,
            "train_number": os.getenv("TRAIN_NUMBER", "12571"),
            "from": os.getenv("FROM_STATION", "BLP"),
            "to": os.getenv("TO_STATION", "ANVT"),
            "journey_date": os.getenv("JOURNEY_DATE", "2026-12-13"),
            "class": os.getenv("TRAVEL_CLASS", "3A"),
            "quota": os.getenv("QUOTA", "GN"),
            "threshold": int(os.getenv("SEAT_THRESHOLD", "20")),
            "available_count": None,
            "message": "No successful check yet. Wait for the scheduled check or trigger POST /api/check-now/."
        })
    return JsonResponse({
        "configured": True,
        "train_number": state.train_number,
        "from": state.from_station,
        "to": state.to_station,
        "journey_date": state.journey_date.isoformat(),
        "class": state.travel_class,
        "quota": state.quota,
        "threshold": state.threshold,
        "available_count": state.available_count,
        "availability_text": state.availability_text,
        "provider_updated_at": state.provider_updated_at.isoformat() if state.provider_updated_at else None,
        "checked_at": state.checked_at.isoformat() if state.checked_at else None,
        "alert_sent": state.alert_sent,
        "last_error": state.last_error,
    })

@csrf_exempt
@require_POST
def check_now(request):
    # Protect this endpoint with your reverse proxy / firewall before exposing it publicly.
    task = check_seat_availability.delay()
    return JsonResponse({"queued": True, "task_id": task.id}, status=202)
