from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import User, Role, Event, Registration
from django.db import connection
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                       AUTHENTICATION
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
class Login(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is None:
            return render(request, "login.html", {"error": "Invalid email or password"})

        login(request, user)

        #redirect by role
        if user.role == Role.ADMIN:
            return redirect("admin_profile")
        elif user.role == Role.EVENT_COORDINATOR:
            return redirect("event_coordinator_profile")
        else:
            return redirect("user_profile")

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("login")

class Signup(View):
    def get(self, request):
        return render(request, "signup.html")

    def post(self, request):
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        role = request.POST.get("role")

        #prevent duplicate accounts using email
        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"error": "Email already exists"})

        if role not in dict(Role.choices):
            return render(request, "signup.html", {"error": "Invalid role"})

        #create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )

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
@login_required
def user_profile(request):
    if request.user.role == Role.ADMIN:
        return redirect("admin_profile")
    elif request.user.role == Role.EVENT_COORDINATOR:
        return redirect("event_coordinator_profile")

    return render(request, "users/user_profile.html", {
        "user": request.user
    })

@login_required
def admin_profile(request):
    if request.user.role != Role.ADMIN:
        return redirect("login")

    return render(request, "users/admin_profile.html", {
        "admin": request.user
    })


@login_required
def event_coordinator_profile(request):
    if request.user.role != Role.EVENT_COORDINATOR:
        return redirect("login")

    events = Event.objects.filter(created_by=request.user).order_by('-event_datetime')

    return render(request, "users/event_coordinator_profile.html", {
        "user": request.user,
        "events": events
    })

def manage_users(request):
    if request.user.role != Role.ADMIN:
        return redirect("home")

    users = User.objects.all()
    return render(request, "users/manage_users.html", {
        "users": users
    })

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
    if request.user.role not in [Role.ADMIN, Role.EVENT_COORDINATOR]:
        return redirect("manage_events")

    if request.method == "POST":
        Event.objects.create(
            created_by=request.user,
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
    if request.user.role not in [Role.ADMIN, Role.EVENT_COORDINATOR]:
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

@login_required
def delete_event(request, event_id):
    if request.user.role not in [Role.ADMIN, Role.EVENT_COORDINATOR]:
        return redirect("home")

    event = get_object_or_404(Event, pk=event_id)
    if request.method == "POST":
        event.delete()
    return redirect("manage_events")

def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    return render(request, "events/event_detail.html", {"event": event})
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                       REGISTRATIONS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def register_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if Registration.objects.filter(recruiter=request.user, event=event).exists():
        return redirect("my_registrations")

    approved_count = Registration.objects.filter(
        event=event,
        status="APPROVED"
    ).count()

    status = "APPROVED" if approved_count < event.capacity else "PENDING"

    Registration.objects.create(
        recruiter=request.user,
        event=event,
        status=status
    )

    return redirect("my_registrations")

def cancel_registration(request, registration_id):
    registration = get_object_or_404(
        Registration,
        pk=registration_id,
        recruiter=request.user
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
    registration.cancelled_by_id = request.user
    registration.save()

    return redirect("my_registrations")

def my_registrations(request):
    # user_id = request.session.get("user_id")
    # if not user_id:
    #     return redirect("login")
    #
    # user = User.objects.get(pk=user_id)

    registrations_qs = Registration.objects.select_related("event").filter(
        recruiter=request.user
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

@login_required
def coordinator_registrations(request):
    if request.user.role != Role.EVENT_COORDINATOR:
        return redirect("home")

    registrations = Registration.objects.select_related("event", "recruiter").filter(
        event__created_by=user
    )

    return render(request, "registrations/coordinator_registrations.html", {
        "registrations": registrations
    })


@login_required
def admin_registrations(request):
    if request.user.role != Role.ADMIN:
        return redirect("home")

    registrations = Registration.objects.select_related("event", "recruiter").all()

    return render(request, "registrations/admin_registrations.html", {
        "registrations": registrations
    })