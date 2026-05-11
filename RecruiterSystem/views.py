from django.shortcuts import render, redirect
from django.views import View
from .models import User, Role
from django.db import connection
from django.contrib.auth import authenticate, login

class Login(View):
    def get(self, request):
        return render(request, "login.html")

    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

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
        request.session.flush()
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