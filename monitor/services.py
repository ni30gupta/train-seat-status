import os
import requests
from django.utils.dateparse import parse_datetime
from http.client import responses

API_URL = "https://ir.railcore.tech/v1/availability/seats"

def fetch_availability():
    api_key = os.getenv("RAILCORE_KEY", "").strip()
    if not api_key:
        raise RuntimeError("RAILCORE_KEY is missing. Add it to .env.")

    params = {
        "train_number": os.getenv("TRAIN_NUMBER", "12571"),
        "from": os.getenv("FROM_STATION", "BLP"),
        "to": os.getenv("TO_STATION", "ANVT"),
        "date": os.getenv("JOURNEY_DATE", "2026-12-13"),
        "class": os.getenv("TRAVEL_CLASS", "3A"),
        "quota": os.getenv("QUOTA", "GN"),
    }
    response = requests.get(
        API_URL,
        params=params,
        headers={"X-RailCore-Key": api_key},
        timeout=25,
    )
    print("response froma rail api............", response)
    response.raise_for_status()
    payload = response.json()

    if payload.get("success") is False:
        raise RuntimeError(f"Availability provider error: {payload}")

    data = payload.get("data", payload)
    classes = data.get("classes") or []
    matching = next(
        (item for item in classes if item.get("class_code") == params["class"]),
        None,
    )
    if not matching:
        raise RuntimeError(f"No {params['class']} class found in API response.")

    count = matching.get("available_count")
    text = matching.get("availability_text") or matching.get("status") or "UNKNOWN"
    updated = parse_datetime(matching.get("last_updated_at") or "")

    # Do not treat WAITLIST/RAC text or missing count as zero seats.
    if count is not None:
        count = int(count)

    return {
        "count": count,
        "text": str(text),
        "provider_updated_at": updated,
        "raw_status": matching.get("status"),
    }


def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
        timeout=20,
    )
    print(response)
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")
