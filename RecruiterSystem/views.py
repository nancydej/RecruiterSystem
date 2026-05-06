from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import User, Event, Registration
from django.shortcuts import get_object_or_404

#++++++++++++++++++++++++++++++++++++++++++++
#                AUTH / USERS
#++++++++++++++++++++++++++++++++++++++++++++
class Login(View):
    def get(self, request):
        return render(request, "login.html")


def user_profile(request):
    user = {}

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users LIMIT 1")
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if row:
            user = dict(zip(columns, row))

    return render(request, "user_profile.html", {"user": user})


def admin_profile(request):
    admin = {}

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE role = 'Admin' LIMIT 1")
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if row:
            admin = dict(zip(columns, row))

    return render(request, "admin_profile.html", {"admin": admin})


def manage_users(request):
    users = []

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        columns = [col[0] for col in cursor.description]

        for row in cursor.fetchall():
            users.append(dict(zip(columns, row)))

    return render(request, "manage_users.html", {"users": users})


def add_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        role = request.POST.get("role")

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users 
                (username, first_name, last_name, email, password, phone_number, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [username, first_name, last_name, email, password, phone_number, role])

        return redirect("manage_users")

    return render(request, "add_user.html")


def edit_user(request, user_id):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        role = request.POST.get("role")

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET username = %s,
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    phone_number = %s,
                    role = %s
                WHERE user_id = %s
            """, [username, first_name, last_name, email, phone_number, role, user_id])

        return redirect("manage_users")

    user = {}

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", [user_id])
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if row:
            user = dict(zip(columns, row))

    return render(request, "edit_user.html", {"user": user})


def delete_user(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE user_id = %s", [user_id])

    return redirect("manage_users")


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                           REGISTRATIONS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#++++++++++++++++++++++++++++++++++++++++++++
#           REGISTER FOR EVENT(S)
#++++++++++++++++++++++++++++++++++++++++++++
def register_event(request, event_id):

    user_id = 3  # TEMP USER
    user = get_object_or_404(User, pk=user_id)
    event = get_object_or_404(Event, pk=event_id)

    # prevent duplicate registration
    exists = Registration.objects.filter(
        recruiter=user,
        event=event
    ).exists()

    if exists:
        return redirect("my_registrations")

    # capacity logic
    approved_count = Registration.objects.filter(
        event=event,
        status="APPROVED"
    ).count()

    if approved_count < event.capacity:
        status = "APPROVED"
    else:
        status = "PENDING"

    Registration.objects.create(
        recruiter=user,
        event=event,
        status=status,
        registration_datetime=timezone.now()
    )

    return redirect("my_registrations")


#++++++++++++++++++++++++++++++++++++++++++++
#           CANCEL REGISTRATION(S)
#++++++++++++++++++++++++++++++++++++++++++++
def cancel_registration(request, registration_id):

    user_id = 3
    registration = get_object_or_404(Registration, pk=registration_id)

    event_date = registration.event.event_datetime

    days_before = (event_date - timezone.now()).days

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

#++++++++++++++++++++++++++++++++++++++++++++
#           VIEW REGISTRATION(S)
#++++++++++++++++++++++++++++++++++++++++++++
def my_registrations(request):

    user_id = 3
    user = get_object_or_404(User, pk=user_id)

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

    return render(request, "my_registrations.html", {
        "registrations": registrations
    })
