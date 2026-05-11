from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("role") != Role.ADMIN:
            raise ValueError("Superuser must have role = Admin")

        return self.create_user(email, password, **extra_fields)

class Role(models.TextChoices):
    ADMIN = "Admin", "Admin"
    EVENT_COORDINATOR = "Event Coordinator", "Event Coordinator"
    RECRUITER = "Recruiter", "Recruiter"

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=Role.choices)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def is_admin(self):
        return self.role == Role.ADMIN

    def is_event_coordinator(self):
        return self.role == Role.EVENT_COORDINATOR

    def is_recruiter(self):
        return self.role == Role.RECRUITER

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        db_table = "users"

class Event(models.Model):
    event_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, db_column='created_by', related_name='created_events')
    event_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    event_datetime = models.DateTimeField()
    capacity = models.IntegerField(validators=[MinValueValidator(3), MaxValueValidator(10)])

    class Meta:
        db_table = "events"

    def __str__(self):
        return f"{self.event_name}"

class RegistrationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    CANCELLED_FULL_REFUND = "CANCELLED_FULL_REFUND", "Cancelled - Full Refund"
    CANCELLED_PARTIAL_REFUND = "CANCELLED_PARTIAL_REFUND", "Cancelled - Partial Refund"
    CANCELLED_NO_REFUND = "CANCELLED_NO_REFUND", "Cancelled - No Refund"

class Registration(models.Model):
    registration_id = models.AutoField(primary_key=True)
    recruiter = models.ForeignKey(User, on_delete=models.PROTECT, db_column='recruiter_id', related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.PROTECT, db_column='event_id', related_name='registrations')
    status = models.CharField(max_length=30, choices=RegistrationStatus.choices, default=RegistrationStatus.PENDING)
    registration_datetime = models.DateTimeField(auto_now_add=True)
    cancel_datetime = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.PROTECT, db_column='cancelled_by', null=True, blank=True, related_name='cancelled_registrations')

    class Meta:
        db_table = "registrations"
        unique_together = ("recruiter", "event")

    def __str__(self):
        return f"Registration {self.registration_id}"
