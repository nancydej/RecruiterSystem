from django.db import models


class User(models.Model):
    user_id = models.AutoField(primary_key=True)

    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Event Coordinator", "Event Coordinator"),
        ("Recruiter", "Recruiter"),
    ]
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    class Meta:
        db_table = "users"


class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    event_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    event_datetime = models.DateTimeField()
    capacity = models.IntegerField()

    class Meta:
        db_table = "events"


class Registration(models.Model):
    registration_id = models.AutoField(primary_key=True)

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("CANCELLED_FULL_REFUND", "CANCELLED_FULL_REFUND"),
        ("CANCELLED_PARTIAL_REFUND", "CANCELLED_PARTIAL_REFUND"),
        ("CANCELLED_NO_REFUND", "CANCELLED_NO_REFUND"),
    ]

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PENDING")
    registration_datetime = models.DateTimeField(auto_now_add=True)
    cancel_datetime = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_registrations"
    )

    class Meta:
        db_table = "registrations"