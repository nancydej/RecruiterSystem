"""
URL configuration for RecruiterSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from RecruiterSystem import views
from RecruiterSystem.views import Login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Login.as_view(), name='login'),

    path('profile/', views.user_profile, name='user_profile'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('register/<int:event_id>/', views.register_event, name='register_event'),
    path('cancel/<int:registration_id>/', views.cancel_registration, name='cancel_registration'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
]
