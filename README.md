# Project Title: Recruiter Event Management System

Course: CS557 - Intro to Database Systems

Group: 5

Names:
- Amber Brellenthin
- Phomany Chanhdara
- Nancy De Jesus
- Saksham Dhirar
- Kelvin Miftar Mahmuti


This project is a Django + MySQL web application for managing recruiter events and registrations.

The system supports three user roles:
- Admin
- Event Coordinator
- Recruiter

Features include:
- Event creation and management
- Recruiter event registration
- Registration approval/cancellation
- MySQL views, triggers, procedures, and functions

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Requirements

Install the following before running the project 
(skip if you already have the following):
  - MySQL Server
  - MySQL Workbench
  - PyCharm / VSCode
  - Any additional required python packages/installations



# Setup Instructions
  1. Clone the Repository using the url (HTTPS)
  2. Create Virtual Environment (varies depending on Windows or Mac/Linux)
  3. Install required packages
  	pip install django mysqlclient

Database setup:
  1. Open MySQL Workbench and connect to your local MySQL server
  2. Run the provided SQL script and execute
  3. Open: recruiter_system/settings.py 
  4. Update this DATABASES section with your MySQL username and password:
   
          DATABASES = {
     
           'default': {

              'ENGINE': 'django.db.backends.mysql',

              'NAME': 'group5',

              'USER': 'your_mysql_username',

              'PASSWORD': 'your_mysql_password',

              'HOST': 'localhost',

              'PORT': '3306',

            }

          } 


# Running the Project:
  1. Start the Django server: python manage.py runserver
  2. When it compiles, it will open the application in your browser
     and provide a link similar to this: http://***.*.*.*:****/ 



# What to Expect?
  Once you log in, users are redirected based on their role:
  Admin -> admin dashboard
  Event Coordinator -> coordinator dashboard
  Recruiter -> event browsing on home page

# Recruiters can:
  1. Browse events
  2. Register for those events
  3. View registrations in “My Registrations”
  4. View registration statuses in the “My Registrations” page
  5. Manage and update their personal profile information

# Event Coordinators can:
  1. Create, edit, and delete events
  2. Manage event capacities and event details
  3. View registrations for their assigned events
  4. Approve or cancel recruiter registrations

# Admins can:
  1. Manage all users
  2. View and manage all registrations + events
  4. Oversee system activity

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Notes
  - Ensure MySQL Server is running before starting Django
  - Verify database credentials in settings.py
  - If pages fail to load, confirm migrations/database setup completed successfully

