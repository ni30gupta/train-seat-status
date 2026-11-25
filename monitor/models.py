from django.db import models

class SeatState(models.Model):
    # One monitored journey in this starter project.
    train_number = models.CharField(max_length=10, unique=True)
    from_station = models.CharField(max_length=10)
    to_station = models.CharField(max_length=10)
    journey_date = models.DateField()
    travel_class = models.CharField(max_length=5)
    quota = models.CharField(max_length=5)
    threshold = models.PositiveIntegerField(default=20)

    available_count = models.IntegerField(null=True, blank=True)
    availability_text = models.CharField(max_length=100, blank=True)
    provider_updated_at = models.DateTimeField(null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    alert_sent = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.train_number}: {self.from_station}-{self.to_station}"
