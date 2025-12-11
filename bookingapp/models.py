from django.db import models
from django.utils import timezone
class UserAccount(models.Model):
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    bonus_bitcoins = models.IntegerField(default=0)
    def __str__(self):
        return self.email
    


class SeatBooking(models.Model):
    movie_name = models.CharField(max_length=100)   # <-- ADD THIS LINE
    seat_label = models.CharField(max_length=10)
    show_date = models.DateField()
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('movie_name', 'show_date', 'seat_label'),)

    def __str__(self):
        return f"{self.movie_name} - {self.show_date} - {self.seat_label}"

