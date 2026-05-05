from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    event_date = models.DateTimeField()
    capacity = models.IntegerField()

    def __str__(self):
        return self.title


class Registration(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Cancelled_Full_Refund', 'Cancelled Full Refund'),
        ('Cancelled_Partial_Refund', 'Cancelled Partial Refund'),
        ('Cancelled_No_Refund', 'Cancelled No Refund'),
    ]

    registration_id = models.AutoField(primary_key=True)

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    registration_datetime = models.DateTimeField(auto_now_add=True)
    cancel_datetime = models.DateTimeField(null=True, blank=True)

    cancelled_by = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('recruiter', 'event')