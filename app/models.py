from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name         = models.CharField(max_length=200)
    start_date   = models.DateField()
    responsible  = models.ForeignKey(User, on_delete=models.CASCADE)
    week_number  = models.CharField(max_length=2, blank=True)
    end_date     = models.DateField()

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        # isocalendar() returns IsoCalendarDate(year, week, weekday) in Python 3.9+
        # index [1] works for both old tuple and new namedtuple
        if not self.week_number:
            iso_week = self.start_date.isocalendar()[1]
            # ISO week can be 1–53; CharField(max_length=2) fits all cases
            self.week_number = str(iso_week)
        super().save(*args, **kwargs)
