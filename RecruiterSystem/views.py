from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import User, Role, Event, Registration
from django.db import connection
from django.utils import timezone

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                       AUTHENTICATION
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
class Login(View):
    def get(self, request):
        return render(request, "auth/login.html")

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.filter(email=email, password=password).first()

        if not user:
            return render(request, "auth/login.html", {"error": "Invalid email or password"})

        request.session["user_id"] = user.user_id
        request.session["role"] = user.role

        # UPDATED FLOW: send everyone to HOME first
        return redirect("home")

class Logout(View):
    def get(self, request):
        request.session.flush()
        return redirect("login")

class Signup(View):
    def get(self, request):
        return render(request, "auth/signup.html")

    def post(self, request):
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        role = request.POST.get("role")

        #prevent duplicate accounts using email
        if User.objects.filter(email=email).exists():
            return render(request, "auth/signup.html", {"error": "Email already exists"})

        #create user
        User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                phone_number=phone_number,
                role=role)

        return redirect("login")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                       HOMEPAGE (PUBLIC)
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def home(request):
    user_id = request.session.get("user_id")

    try:
        events = Event.objects.all()
    except Exception:
        events = []  # fallback if DB fails

    return render(request, "home.html", {
        "events": events,
        "user_id": user_id
    })

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                           USERS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def user_profile(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return redirect("login")

    return render(request, "users/user_profile.html", {"user": user})

def admin_profile(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    admin = User.objects.filter(
        user_id=user_id,
        role=Role.ADMIN
    ).first()

    if not admin:
        return redirect("login")

    return render(request, "users/admin_profile.html", {"admin": admin})


def manage_users(request):
    users = User.objects.all()
    return render(request, "users/manage_users.html", {"users": users})


def add_user(request):
    if request.method == "POST":
        User.objects.create(
            username=request.POST.get("username"),
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            email=request.POST.get("email"),
            password=request.POST.get("password"),
            phone_number=request.POST.get("phone_number"),
            role=request.POST.get("role"),
        )
        return redirect("manage_users")
    return render(request, "users/add_user.html")


def edit_user(request, user_id):
    user = get_object_or_404(User, user_id=user_id)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone_number = request.POST.get("phone_number")
        user.role = request.POST.get("role")
        user.save()
        return redirect("manage_users")

    return render(request, "users/edit_user.html", {"user": user})

def delete_user(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    user.delete()
    return redirect("manage_users")


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                      MANAGE EVENT - CRUD
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def manage_events(request):
    events = Event.objects.select_related('created_by').all()
    return render(request, "events/manage_events.html", {"events": events})


def add_event(request):
    role = request.session.get("role")
    if role not in ["Admin", "Event Coordinator"]:
        return redirect("manage_events")

    if request.method == "POST":
        Event.objects.create(
            created_by_id=request.session.get("user_id"),
            event_name=request.POST.get("event_name"),
            description=request.POST.get("description"),
            city=request.POST.get("city"),
            state=request.POST.get("state"),
            event_datetime=request.POST.get("event_datetime"),
            capacity=request.POST.get("capacity"),
        )
        return redirect("manage_events")

    return render(request, "events/add_event.html")


def edit_event(request, event_id):
    role = request.session.get("role")
    if role not in ["Admin", "Event Coordinator"]:
        return redirect("manage_events")

    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        event.event_name = request.POST.get("event_name")
        event.description = request.POST.get("description")
        event.city = request.POST.get("city")
        event.state = request.POST.get("state")
        event.event_datetime = request.POST.get("event_datetime")
        event.capacity = request.POST.get("capacity")
        event.save()
        return redirect("manage_events")

    return render(request, "events/edit_event.html", {"event": event})


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                       REGISTRATIONS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def register_event(request, event_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = get_object_or_404(User, pk=user_id)
    event = get_object_or_404(Event, pk=event_id)

    # prevent duplicate registration
    if Registration.objects.filter(recruiter=user, event=event).exists():
        return redirect("my_registrations")

    # capacity logic
    approved_count = Registration.objects.filter(
        event=event,
        status="APPROVED"
    ).count()

    status = "APPROVED" if approved_count < event.capacity else "PENDING"

    Registration.objects.create(
        recruiter=user,
        event=event,
        status=status
    )

    return redirect("my_registrations")

def cancel_registration(request, registration_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    registration = get_object_or_404(
        Registration,
        pk=registration_id,
        recruiter_id=user_id
    )

    # prevent cancelling twice
    if registration.status.startswith("CANCELLED"):
        return redirect("my_registrations")

    event_date = registration.event.event_datetime
    days_before = (event_date.date() - timezone.now().date()).days

    if days_before >= 14:
        status = "CANCELLED_FULL_REFUND"
    elif 7 <= days_before < 14:
        status = "CANCELLED_PARTIAL_REFUND"
    else:
        status = "CANCELLED_NO_REFUND"

    registration.status = status
    registration.cancel_datetime = timezone.now()
    registration.cancelled_by_id = user_id
    registration.save()

    return redirect("my_registrations")

def my_registrations(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = User.objects.get(pk=user_id)

    registrations_qs = Registration.objects.select_related("event").filter(
        recruiter=user
    )

    registrations = []

    for r in registrations_qs:
        registrations.append({
            "registration_id": r.registration_id,
            "event_name": r.event.event_name,
            "status": r.status,
            "registration_datetime": r.registration_datetime,
        })

    return render(request, "registrations/my_registrations.html", {
        "registrations": registrations
    })