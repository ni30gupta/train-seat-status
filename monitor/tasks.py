import os
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import SeatState
from .services import fetch_availability, send_telegram
from cgitb import reset

@shared_task
def check_seat_availability():
    state = SeatState.objects.first()
    if state is None:
        from datetime import date
        state = SeatState.objects.create(
            train_number=os.getenv("TRAIN_NUMBER", "12571"),
            from_station=os.getenv("FROM_STATION", "BLP"),
            to_station=os.getenv("TO_STATION", "ANVT"),
            journey_date=date.fromisoformat(os.getenv("JOURNEY_DATE", "2026-12-13")),
            travel_class=os.getenv("TRAVEL_CLASS", "3A"),
            quota=os.getenv("QUOTA", "GN"),
            threshold=int(os.getenv("SEAT_THRESHOLD", "270")),
        )

    try:
        result = fetch_availability()
        print('fetch_availablity resultt...', result)
        count = result["count"]
        if count is None:
            raise RuntimeError(
                f"Provider did not return a numeric available_count: {result['text']}"
            )

        now = timezone.now()
        should_alert = count <= state.threshold 

        # Persist the latest reading only. Do not keep a long-term history of live API data.
        with transaction.atomic():
            state.available_count = count
            state.availability_text = result["text"]
            state.provider_updated_at = result["provider_updated_at"]
            state.checked_at = now
            state.last_error = ""
            state.save()

        if should_alert:
            message = (
                "🚆 Train seat alert!\n"
                f"Train: {state.train_number}\n"
                f"Journey: {state.journey_date}\n"
                f"Route: {state.from_station} → {state.to_station}\n"
                f"Class/quota: {state.travel_class} / {state.quota}\n"
                f"Available: {count} (threshold: ≤ {state.threshold})\n"
                f"Checked: {timezone.localtime(now).strftime('%d-%m-%Y %I:%M %p IST')}\n"
                "Please verify on IRCTC before booking."
            )
            try:
                send_telegram(message)
            except Exception:
                # Permit the next run to retry delivery if Telegram failed.
                state.alert_sent = False
                state.last_error = "Telegram delivery failed; next scheduled run will retry."
                state.save(update_fields=["alert_sent", "last_error", "updated_at"])
                raise

        return {"available_count": count, "alert_sent_now": should_alert}

    except Exception as exc:
        state.last_error = str(exc)[:2000]
        state.checked_at = timezone.now()
        state.save(update_fields=["last_error", "checked_at", "updated_at"])
        raise
