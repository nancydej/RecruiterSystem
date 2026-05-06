from django.shortcuts import render, redirect
from django.views.generic import View
from django.db import connection

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

    #+++++++++++++++ TEMP USER (LOGIN NOT IMPLEMENTED) +++++++++++++++
    user_id = 3  # Recruiter example ID

    with connection.cursor() as cursor:

        #+++++++++++++++ prevent duplicate registration +++++++++++++++
        cursor.execute("""
            SELECT 1 FROM registrations
            WHERE recruiter_id = %s AND event_id = %s
        """, [user_id, event_id])

        if cursor.fetchone():
            return redirect("my_registrations")

        #+++++++++++++++ get event capacity +++++++++++++++
        cursor.execute("""
            SELECT capacity FROM events WHERE event_id = %s
        """, [event_id])
        capacity = cursor.fetchone()[0]

        #+++++++++++++++ count approved registrations +++++++++++++++
        cursor.execute("""
            SELECT COUNT(*) FROM registrations
            WHERE event_id = %s AND status = 'Approved'
        """, [event_id])
        approved_count = cursor.fetchone()[0]

        #+++++++++++++++ decide status +++++++++++++++
        if approved_count < capacity:
            status = "Approved"
        else:
            status = "Pending"

        #+++++++++++++++ insert registration +++++++++++++++
        cursor.execute("""
            INSERT INTO registrations
            (recruiter_id, event_id, status, registration_datetime)
            VALUES (%s, %s, %s, NOW())
        """, [user_id, event_id, status])

    return redirect("my_registrations")


#++++++++++++++++++++++++++++++++++++++++++++
#           CANCEL REGISTRATION(S)
#++++++++++++++++++++++++++++++++++++++++++++
def cancel_registration(request, registration_id):

    user_id = 3  # TEMP USER

    with connection.cursor() as cursor:

        #+++++++++++++++ get event date +++++++++++++++
        cursor.execute("""
            SELECT e.event_date
            FROM events e
            JOIN registrations r ON e.event_id = r.event_id
            WHERE r.registration_id = %s
        """, [registration_id])

        result = cursor.fetchone()

        if not result:
            return redirect("my_registrations")

        event_date = result[0]

        #+++++++++++++++ calculate days before event +++++++++++++++
        cursor.execute("SELECT DATEDIFF(%s, NOW())", [event_date])
        days_before = cursor.fetchone()[0]

        #+++++++++++++++ refund logic +++++++++++++++
        if days_before >= 14:
            status = "Cancelled_Full_Refund"
        elif 7 <= days_before < 14:
            status = "Cancelled_Partial_Refund"
        else:
            status = "Cancelled_No_Refund"

        #+++++++++++++++ update registration +++++++++++++++
        cursor.execute("""
            UPDATE registrations
            SET status = %s,
                cancel_datetime = NOW(),
                cancelled_by = 'recruiter'
            WHERE registration_id = %s
        """, [status, registration_id])

    return redirect("my_registrations")

#++++++++++++++++++++++++++++++++++++++++++++
#           VIEW REGISTRATION(S)
#++++++++++++++++++++++++++++++++++++++++++++
def my_registrations(request):

    user_id = 3  # TEMP USER

    registrations = []

    with connection.cursor() as cursor:

        #+++++++++++++++ fetch user registrations +++++++++++++++
        cursor.execute("""
            SELECT r.registration_id, e.event_name, r.status, r.registration_datetime
            FROM registrations r
            JOIN events e ON r.event_id = e.event_id
            WHERE r.recruiter_id = %s
        """, [user_id])

        columns = [col[0] for col in cursor.description]

        for row in cursor.fetchall():
            registrations.append(dict(zip(columns, row)))

    return render(request, "my_registrations.html", {
        "registrations": registrations
    })

