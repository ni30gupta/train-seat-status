from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check-seat-availability-every-3-hours": {
        "task": "monitor.tasks.check_seat_availability",
        # "schedule": crontab(minute="*"),
        "schedule": crontab(minute=0, hour="*/3"),
    },
}